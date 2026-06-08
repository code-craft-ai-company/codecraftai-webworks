"""
.. module:: validation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OpenAPI specification validation utilities.

.. moduleauthor:: Code Craft AI LLC

This module provides validation classes for verifying OpenAPI 3.0+
specifications. It includes:

- :class:`ValidationIssue` - A dataclass representing a single validation issue.
- :class:`SpecificationValidationError` - An exception raised when validation fails.
- :class:`OpenAPIValidator` - A validator that checks structure, references, and
  security scheme consistency of an OpenAPI specification.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationIssue:
    """
        Represents a single validation issue found in an OpenAPI specification.

        :param path: JSON path to the issue location (e.g. ``"paths./users.get"``).
        :param message: A human-readable description of the issue.
        :param severity: The severity level, either ``"error"`` or ``"warning"``.
    """

    path: str
    message: str
    severity: str  # "error" or "warning"


class SpecificationValidationError(Exception):
    """
        Raised when OpenAPI specification validation fails.

        Stores the list of :class:`ValidationIssue` objects that caused the
        failure and formats a summary message indicating the number of issues.

        :param issues: A list of :class:`ValidationIssue` objects.
    """

    def __init__(self, issues: List[ValidationIssue]):
        self.issues = issues
        message = f"OpenAPI specification validation failed with {len(issues)} issue(s)"
        super().__init__(message)


class OpenAPIValidator:
    """
        Validates OpenAPI 3.0+ specifications for structural correctness,
        reference resolution, and security scheme consistency.

        When ``strict`` is True, the validator also checks for missing
        descriptions on operations and missing examples on schemas, and
        treats all warnings as errors.

        :param strict: If True, enable strict validation mode.
    """

    def __init__(self, strict: bool = False):
        self.strict = strict
        return

    def validate(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """
            Validate an OpenAPI specification dictionary.

            Runs structural validation, ``$ref`` resolution validation, and
            security scheme reference validation. In strict mode, also checks
            for missing descriptions and examples.

            :param spec: An OpenAPI specification dictionary.

            :returns: A list of :class:`ValidationIssue` objects found during
                validation. If no errors are found, the list contains only
                warnings (if any).

            :raises SpecificationValidationError: If validation errors are found.
        """
        issues: List[ValidationIssue] = []

        issues.extend(self._validate_structure(spec))
        issues.extend(self._validate_refs(spec))
        issues.extend(self._validate_security(spec))

        if self.strict:
            issues.extend(self._validate_strict(spec))

        errors = [i for i in issues if i.severity == "error"]

        if self.strict:
            # In strict mode, treat all issues (including warnings) as errors
            errors = list(issues)

        if len(errors) > 0:
            raise SpecificationValidationError(errors)

        return issues

    def _validate_structure(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """
            Validate the basic structural requirements of an OpenAPI specification.

            Checks that the required top-level fields ``openapi``, ``info``,
            ``info.title``, ``info.version``, and ``paths`` are present.

            :param spec: An OpenAPI specification dictionary.

            :returns: A list of structural validation issues.
        """
        issues: List[ValidationIssue] = []

        # Check required top-level field: openapi
        if "openapi" not in spec:
            issue = ValidationIssue(
                path="openapi",
                message="Missing required field 'openapi'",
                severity="error",
            )
            issues.append(issue)

        # Check required top-level field: info
        if "info" not in spec:
            issue = ValidationIssue(
                path="info",
                message="Missing required field 'info'",
                severity="error",
            )
            issues.append(issue)
        else:
            info = spec["info"]

            # Check required info field: title
            if "title" not in info:
                issue = ValidationIssue(
                    path="info.title",
                    message="Missing required field 'info.title'",
                    severity="error",
                )
                issues.append(issue)

            # Check required info field: version
            if "version" not in info:
                issue = ValidationIssue(
                    path="info.version",
                    message="Missing required field 'info.version'",
                    severity="error",
                )
                issues.append(issue)

        # Check required top-level field: paths
        if "paths" not in spec:
            issue = ValidationIssue(
                path="paths",
                message="Missing required field 'paths'",
                severity="error",
            )
            issues.append(issue)

        return issues

    def _validate_refs(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """
            Validate that all ``$ref`` values resolve to existing schemas in
            ``components/schemas``.

            Walks the entire specification dictionary tree and collects all
            ``$ref`` values that point to ``#/components/schemas/...``, then
            verifies each referenced schema name exists.

            :param spec: An OpenAPI specification dictionary.

            :returns: A list of reference resolution issues.
        """
        issues: List[ValidationIssue] = []

        defined_schemas = set()
        components = spec.get("components", {})
        schemas_section = components.get("schemas", {})
        for schema_name in schemas_section:
            defined_schemas.add(schema_name)

        # Collect all $ref values from the spec
        ref_locations = self._collect_refs(spec, "")

        for ref_path, ref_value in ref_locations:
            if not ref_value.startswith("#/components/schemas/"):
                continue

            schema_name = ref_value.replace("#/components/schemas/", "")
            if schema_name not in defined_schemas:
                issue = ValidationIssue(
                    path=ref_path,
                    message=f"$ref '{ref_value}' references undefined schema '{schema_name}'",
                    severity="error",
                )
                issues.append(issue)

        return issues

    def _collect_refs(self, obj: Any, current_path: str) -> List[tuple]:
        """
            Recursively collect all ``$ref`` values and their JSON paths from
            a nested dictionary/list structure.

            :param obj: The current object being traversed.
            :param current_path: The JSON path to the current object.

            :returns: A list of (path, ref_value) tuples.
        """
        refs: List[tuple] = []

        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_value = obj["$ref"]
                refs.append((current_path, ref_value))

            for key, value in obj.items():
                if key == "$ref":
                    continue
                child_path = f"{current_path}.{key}" if current_path else key
                refs.extend(self._collect_refs(value, child_path))

        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                child_path = f"{current_path}[{index}]"
                refs.extend(self._collect_refs(item, child_path))

        return refs

    def _validate_security(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """
            Validate that all security requirements reference schemes defined
            in ``components/securitySchemes``.

            Iterates all operations in the paths and checks that each security
            requirement object references a scheme name that exists in the
            ``components/securitySchemes`` section.

            :param spec: An OpenAPI specification dictionary.

            :returns: A list of security reference issues.
        """
        issues: List[ValidationIssue] = []

        components = spec.get("components", {})
        defined_schemes = set(components.get("securitySchemes", {}).keys())

        paths = spec.get("paths", {})
        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                security_reqs = operation.get("security")
                if security_reqs is None:
                    continue

                for req_obj in security_reqs:
                    if not isinstance(req_obj, dict):
                        continue

                    for scheme_name in req_obj:
                        if scheme_name not in defined_schemes:
                            issue_path = f"paths.{path_str}.{method}.security"
                            issue = ValidationIssue(
                                path=issue_path,
                                message=(
                                    f"Security requirement references undefined "
                                    f"scheme '{scheme_name}'"
                                ),
                                severity="error",
                            )
                            issues.append(issue)

        return issues

    def _validate_strict(self, spec: Dict[str, Any]) -> List[ValidationIssue]:
        """
            Perform strict mode validation checks.

            In strict mode, checks for:
            - Missing ``description`` on operations.
            - Missing ``example`` on schemas in ``components/schemas``.

            Issues found by this method are reported as warnings.

            :param spec: An OpenAPI specification dictionary.

            :returns: A list of strict mode validation issues.
        """
        issues: List[ValidationIssue] = []

        # Check for missing descriptions on operations
        paths = spec.get("paths", {})
        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                if "description" not in operation:
                    issue_path = f"paths.{path_str}.{method}.description"
                    issue = ValidationIssue(
                        path=issue_path,
                        message=f"Operation {method.upper()} {path_str} is missing a description",
                        severity="warning",
                    )
                    issues.append(issue)

        # Check for missing examples on schemas
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        for schema_name, schema_def in schemas.items():
            if not isinstance(schema_def, dict):
                continue

            if "example" not in schema_def:
                issue_path = f"components.schemas.{schema_name}.example"
                issue = ValidationIssue(
                    path=issue_path,
                    message=f"Schema '{schema_name}' is missing an example",
                    severity="warning",
                )
                issues.append(issue)

        return issues
