"""
    Verification tests for the blueprintdemo test site bundled asset serving.

    This module confirms that the blueprintdemo site's Swagger UI page
    loads entirely from bundled local assets with no external CDN
    references.  It exercises the same SwaggerUIBlueprint configuration
    used in ``source/testsites/blueprintdemo/app.py`` and verifies that
    every ``src`` and ``href`` attribute in the generated HTML resolves
    to a servable local asset.

    **Validates: Requirements 8.4, 8.5**
"""

import re

from ccai.testbase.mocking import Mock

from ccai.webworks.openapi.configuration import OpenAPIInfo
from ccai.webworks.openapi.swaggerui import SwaggerUIBlueprint


# =============================================================================
# Helper Functions
# =============================================================================

def _create_blueprintdemo_swagger_ui():
    """
        Create a SwaggerUIBlueprint configured identically to the
        blueprintdemo test site in ``source/testsites/blueprintdemo/app.py``.

        :returns: A SwaggerUIBlueprint instance matching the demo config.
    """
    mock_generator = Mock()
    mock_generator.configure(recursive=True)

    info = OpenAPIInfo(
        title="Blueprint Demo API",
        version="1.0.0",
        description="Demonstrates RestBlueprint patterns with Swagger UI.",
    )
    ctx = mock_generator.mock_context()
    ctx.set_attribute("info", info)
    ctx.mock_method("generate_json", return_value='{"openapi":"3.0.3","info":{"title":"Blueprint Demo API","version":"1.0.0"},"paths":{}}')

    swagger_ui = SwaggerUIBlueprint(
        generator=mock_generator,
        ui_path="/docs",
        spec_path="/openapi.json",
    )

    return swagger_ui


_EXTERNAL_DOMAIN_PATTERN = re.compile(
    r'(?:src|href)\s*=\s*["\']https?://',
    re.IGNORECASE,
)

_CDN_INDICATORS = [
    "unpkg.com",
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "cdn.redoc.ly",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
]


# =============================================================================
# Verification Tests
# =============================================================================

def test_blueprintdemo_swagger_html_has_no_external_references():
    """
        Verify that the Swagger UI HTML generated with the blueprintdemo
        configuration contains no ``src`` or ``href`` attributes pointing
        to external domains.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    html, status_code, _ = swagger_ui.serve_ui()

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    matches = _EXTERNAL_DOMAIN_PATTERN.findall(html)
    if matches:
        errmsg = (
            f"Swagger UI HTML contains external domain references: {matches}"
        )
        raise AssertionError(errmsg)

    return


def test_blueprintdemo_swagger_html_has_no_cdn_indicators():
    """
        Verify that the Swagger UI HTML contains no known CDN hostnames.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    html, _, _ = swagger_ui.serve_ui()

    for indicator in _CDN_INDICATORS:
        if indicator in html:
            errmsg = (
                f"Swagger UI HTML contains CDN reference '{indicator}'"
            )
            raise AssertionError(errmsg)

    return


def test_blueprintdemo_swagger_html_references_local_swagger_assets():
    """
        Verify that the generated HTML references the bundled Swagger UI
        assets via the local ``/_swagger/`` path prefix.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    html, _, _ = swagger_ui.serve_ui()

    expected_refs = [
        "/_swagger/swagger-ui-bundle.js",
        "/_swagger/swagger-ui.css",
        "/_swagger/favicon-32x32.png",
    ]

    for ref in expected_refs:
        if ref not in html:
            errmsg = f"Expected HTML to reference '{ref}'"
            raise AssertionError(errmsg)

    return


def test_blueprintdemo_serve_static_resolves_swagger_ui_bundle_js():
    """
        Verify that serve_static successfully resolves swagger-ui-bundle.js
        from the vendored assets.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    content, status_code, headers = swagger_ui.serve_static("swagger-ui-bundle.js")

    if status_code != 200:
        errmsg = f"Expected status 200 for swagger-ui-bundle.js, got {status_code}"
        raise AssertionError(errmsg)

    if not isinstance(content, bytes) or len(content) == 0:
        errmsg = "Expected non-empty bytes content for swagger-ui-bundle.js"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "application/javascript":
        errmsg = f"Expected Content-Type 'application/javascript', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_blueprintdemo_serve_static_resolves_swagger_ui_css():
    """
        Verify that serve_static successfully resolves swagger-ui.css
        from the vendored assets.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    content, status_code, headers = swagger_ui.serve_static("swagger-ui.css")

    if status_code != 200:
        errmsg = f"Expected status 200 for swagger-ui.css, got {status_code}"
        raise AssertionError(errmsg)

    if not isinstance(content, bytes) or len(content) == 0:
        errmsg = "Expected non-empty bytes content for swagger-ui.css"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "text/css":
        errmsg = f"Expected Content-Type 'text/css', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_blueprintdemo_serve_static_resolves_favicon():
    """
        Verify that serve_static successfully resolves favicon-32x32.png
        from the vendored assets.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    content, status_code, headers = swagger_ui.serve_static("favicon-32x32.png")

    if status_code != 200:
        errmsg = f"Expected status 200 for favicon-32x32.png, got {status_code}"
        raise AssertionError(errmsg)

    if not isinstance(content, bytes) or len(content) == 0:
        errmsg = "Expected non-empty bytes content for favicon-32x32.png"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "image/png":
        errmsg = f"Expected Content-Type 'image/png', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_blueprintdemo_serve_static_sets_cache_control():
    """
        Verify that serve_static sets Cache-Control headers for immutable
        caching on all bundled assets.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()

    asset_files = [
        "swagger-ui-bundle.js",
        "swagger-ui.css",
        "favicon-32x32.png",
    ]

    expected_cache = "public, max-age=31536000, immutable"

    for filename in asset_files:
        _, status_code, headers = swagger_ui.serve_static(filename)

        if status_code != 200:
            errmsg = f"Expected status 200 for {filename}, got {status_code}"
            raise AssertionError(errmsg)

        actual_cache = headers.get("Cache-Control")
        if actual_cache != expected_cache:
            errmsg = (
                f"Expected Cache-Control '{expected_cache}' for {filename}, "
                f"got {actual_cache!r}"
            )
            raise AssertionError(errmsg)

    return


def test_blueprintdemo_serve_static_returns_404_for_unknown_file():
    """
        Verify that serve_static returns 404 for files not in the bundle.
    """
    swagger_ui = _create_blueprintdemo_swagger_ui()
    _, status_code, _ = swagger_ui.serve_static("nonexistent-file.js")

    if status_code != 404:
        errmsg = f"Expected status 404 for nonexistent file, got {status_code}"
        raise AssertionError(errmsg)

    return


def test_blueprintdemo_serve_spec_returns_valid_json():
    """
        Verify that serve_spec returns valid JSON with the expected
        OpenAPI structure.
    """
    import json

    swagger_ui = _create_blueprintdemo_swagger_ui()
    json_str, status_code, headers = swagger_ui.serve_spec()

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "application/json":
        errmsg = f"Expected Content-Type 'application/json', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    spec = json.loads(json_str)

    if "openapi" not in spec:
        errmsg = "Expected 'openapi' key in specification"
        raise AssertionError(errmsg)

    return
