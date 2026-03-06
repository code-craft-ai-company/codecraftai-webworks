"""
    Property test for Swagger UI and ReDoc self-containment.

    This module verifies Property 1: Self-Containment.

    For generated Swagger UI and ReDoc HTML, no ``src`` or ``href``
    attributes SHALL reference external domains.  All asset references
    SHALL use relative paths pointing to the application's own static
    asset endpoints.

    **Validates: Requirements 8.4, 8.5, 12.3, 12.4**
"""

import re

from automojo.testbase.mocking import Mock

from automojo.webworks.openapi.configuration import OpenAPIInfo
from automojo.webworks.openapi.redoc import ReDocBlueprint
from automojo.webworks.openapi.swaggerui import SwaggerUIBlueprint


# =============================================================================
# Helper Functions
# =============================================================================

def _create_mock_generator(title="Test API", version="1.0.0"):
    """
        Create a mock OpenAPI_Generator with configurable info.

        :param title: The API title for the info object.
        :param version: The API version for the info object.

        :returns: A configured Mock object acting as an OpenAPI_Generator.
    """
    mock_generator = Mock()
    mock_generator.configure(recursive=True)

    info = OpenAPIInfo(title=title, version=version)
    ctx = mock_generator.mock_context()
    ctx.set_attribute("info", info)
    ctx.mock_method("generate_json", return_value='{"openapi":"3.0.3"}')

    return mock_generator


# =============================================================================
# Test Data
# =============================================================================

# Various configuration combinations to exercise the HTML template
# with different static_path values, titles, and options.

_SELF_CONTAINMENT_CASES = [
    {
        "title": "Default Config API",
        "static_path": "/_swagger",
        "try_it_out": True,
        "doc_expansion": "list",
        "filter": True,
    },
    {
        "title": "Custom Path API",
        "static_path": "/assets/swagger",
        "try_it_out": False,
        "doc_expansion": "none",
        "filter": False,
    },
    {
        "title": "Deep Path API",
        "static_path": "/api/v1/static/swagger-ui",
        "try_it_out": True,
        "doc_expansion": "full",
        "filter": True,
    },
    {
        "title": "Minimal API",
        "static_path": "/s",
        "try_it_out": False,
        "doc_expansion": "list",
        "filter": False,
    },
    {
        "title": "Special Chars API <>&",
        "static_path": "/_swagger",
        "try_it_out": True,
        "doc_expansion": "list",
        "filter": True,
    },
    {
        "title": "Production API",
        "static_path": "/docs/static",
        "try_it_out": False,
        "doc_expansion": "none",
        "filter": True,
    },
    {
        "title": "Staging API",
        "static_path": "/_swagger",
        "try_it_out": True,
        "doc_expansion": "full",
        "filter": False,
    },
    {
        "title": "Internal API",
        "static_path": "/internal/swagger-assets",
        "try_it_out": True,
        "doc_expansion": "list",
        "filter": True,
    },
    {
        "title": "Public API",
        "static_path": "/public/assets",
        "try_it_out": False,
        "doc_expansion": "none",
        "filter": False,
    },
    {
        "title": "Test API v2",
        "static_path": "/_swagger",
        "try_it_out": True,
        "doc_expansion": "list",
        "filter": True,
    },
]

# Regex to find src="..." and href="..." attribute values
_SRC_HREF_PATTERN = re.compile(
    r'(?:src|href)\s*=\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Known external domain indicators
_EXTERNAL_INDICATORS = [
    "http://",
    "https://",
    "//unpkg.com",
    "//cdn.jsdelivr.net",
    "//cdnjs.cloudflare.com",
    "//cdn.redoc.ly",
    "//fonts.googleapis.com",
    "//fonts.gstatic.com",
]


# =============================================================================
# Property Test
# =============================================================================

def test_property_swagger_ui_self_containment():
    """
        **Validates: Requirements 8.4, 8.5**

        Property 1: Self-Containment

        For generated Swagger UI HTML, verify no ``src`` or ``href``
        attributes reference external domains.  All asset references
        must use relative paths only.

        This test iterates over multiple configuration combinations to
        ensure the property holds regardless of static_path, title, or
        Swagger UI options.
    """
    total_cases = len(_SELF_CONTAINMENT_CASES)
    total_checks = 0

    for case_entry in _SELF_CONTAINMENT_CASES:
        title = case_entry["title"]
        static_path = case_entry["static_path"]
        try_it_out = case_entry["try_it_out"]
        doc_expansion = case_entry["doc_expansion"]
        filter_val = case_entry["filter"]

        generator = _create_mock_generator(title=title)
        blueprint = SwaggerUIBlueprint(
            generator=generator,
            static_path=static_path,
            try_it_out=try_it_out,
            doc_expansion=doc_expansion,
            filter=filter_val,
        )

        html = blueprint._build_swagger_html()

        # Extract all src and href attribute values
        matches = _SRC_HREF_PATTERN.findall(html)

        for attr_value in matches:
            for indicator in _EXTERNAL_INDICATORS:
                if indicator in attr_value:
                    errmsg = (
                        "Self-containment violation for config "
                        "(title={}, static_path={}): "
                        "found external reference '{}'"
                    ).format(title, static_path, attr_value)
                    raise AssertionError(errmsg)

            total_checks += 1

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = "Expected at least 10 test cases, got {}".format(total_cases)
        raise AssertionError(errmsg)

    if total_checks < 10:
        errmsg = "Expected at least 10 attribute checks, got {}".format(total_checks)
        raise AssertionError(errmsg)

    return


# =============================================================================
# ReDoc Test Data
# =============================================================================

# Various configuration combinations to exercise the ReDoc HTML template
# with different static_path values, titles, and options.

_REDOC_SELF_CONTAINMENT_CASES = [
    {
        "title": "Default Config API",
        "static_path": "/_redoc",
    },
    {
        "title": "Custom Path API",
        "static_path": "/assets/redoc",
    },
    {
        "title": "Deep Path API",
        "static_path": "/api/v1/static/redoc",
    },
    {
        "title": "Minimal API",
        "static_path": "/r",
    },
    {
        "title": "Special Chars API <>&",
        "static_path": "/_redoc",
    },
    {
        "title": "Production API",
        "static_path": "/docs/redoc-static",
    },
    {
        "title": "Staging API",
        "static_path": "/_redoc",
    },
    {
        "title": "Internal API",
        "static_path": "/internal/redoc-assets",
    },
    {
        "title": "Public API",
        "static_path": "/public/redoc",
    },
    {
        "title": "Test API v2",
        "static_path": "/_redoc",
    },
]


# =============================================================================
# ReDoc Property Test
# =============================================================================

def test_property_redoc_self_containment():
    """
        **Validates: Requirements 12.3, 12.4**

        Property 1: Self-Containment (ReDoc)

        For generated ReDoc HTML, verify no ``src`` or ``href``
        attributes reference external domains.  All asset references
        must use relative paths only.

        This test iterates over multiple configuration combinations to
        ensure the property holds regardless of static_path, title, or
        ReDoc options.
    """
    total_cases = len(_REDOC_SELF_CONTAINMENT_CASES)
    total_checks = 0

    for case_entry in _REDOC_SELF_CONTAINMENT_CASES:
        title = case_entry["title"]
        static_path = case_entry["static_path"]

        generator = _create_mock_generator(title=title)
        blueprint = ReDocBlueprint(
            generator=generator,
            static_path=static_path,
        )

        html = blueprint._build_redoc_html()

        # Extract all src and href attribute values
        matches = _SRC_HREF_PATTERN.findall(html)

        for attr_value in matches:
            for indicator in _EXTERNAL_INDICATORS:
                if indicator in attr_value:
                    errmsg = (
                        "Self-containment violation for ReDoc config "
                        "(title={}, static_path={}): "
                        "found external reference '{}'"
                    ).format(title, static_path, attr_value)
                    raise AssertionError(errmsg)

            total_checks += 1

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = "Expected at least 10 test cases, got {}".format(total_cases)
        raise AssertionError(errmsg)

    if total_checks < 10:
        errmsg = "Expected at least 10 attribute checks, got {}".format(total_checks)
        raise AssertionError(errmsg)

    return
