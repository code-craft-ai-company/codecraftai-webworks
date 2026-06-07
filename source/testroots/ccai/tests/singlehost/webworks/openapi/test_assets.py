"""
    Unit tests for the AssetResolver class in the OpenAPI assets module.

    This module tests the AssetResolver class including file resolution,
    Content-Type mapping, integrity verification, and version properties.

    **Validates: Requirements 7.1, 7.2, 7.5, 7.6, 8.8**
"""

from ccai.webworks.openapi.assets import AssetResolver


# =============================================================================
# Unit Tests for AssetResolver Initialization
# =============================================================================

def test_asset_resolver_creates_successfully():
    """
        Verify that AssetResolver can be instantiated without errors.
    """
    resolver = AssetResolver()

    assert resolver is not None

    return


def test_asset_resolver_loads_manifest():
    """
        Verify that AssetResolver loads the manifest on initialization.
    """
    resolver = AssetResolver()

    version = resolver.swagger_ui_version

    assert version is not None

    return


# =============================================================================
# Unit Tests for resolve()
# =============================================================================

def test_resolve_returns_bytes_for_swagger_ui_bundle_js():
    """
        Verify that resolve returns bytes for the swagger-ui-bundle.js file.
    """
    resolver = AssetResolver()

    content = resolver.resolve("swagger-ui", "swagger-ui-bundle.js")

    assert content is not None
    assert isinstance(content, bytes)
    assert len(content) > 0

    return


def test_resolve_returns_bytes_for_swagger_ui_css():
    """
        Verify that resolve returns bytes for the swagger-ui.css file.
    """
    resolver = AssetResolver()

    content = resolver.resolve("swagger-ui", "swagger-ui.css")

    assert content is not None
    assert isinstance(content, bytes)
    assert len(content) > 0

    return


def test_resolve_returns_bytes_for_favicon():
    """
        Verify that resolve returns bytes for the favicon-32x32.png file.
    """
    resolver = AssetResolver()

    content = resolver.resolve("swagger-ui", "favicon-32x32.png")

    assert content is not None
    assert isinstance(content, bytes)
    assert len(content) > 0

    return


def test_resolve_returns_bytes_for_redoc_standalone_js():
    """
        Verify that resolve returns bytes for the redoc.standalone.js file.
    """
    resolver = AssetResolver()

    content = resolver.resolve("redoc", "redoc.standalone.js")

    assert content is not None
    assert isinstance(content, bytes)
    assert len(content) > 0

    return


def test_resolve_returns_none_for_nonexistent_file():
    """
        Verify that resolve returns None for a file that does not exist.
    """
    resolver = AssetResolver()

    content = resolver.resolve("swagger-ui", "nonexistent-file.js")

    assert content is None

    return


def test_resolve_returns_none_for_nonexistent_group():
    """
        Verify that resolve returns None for an asset group that does not exist.
    """
    resolver = AssetResolver()

    content = resolver.resolve("nonexistent-group", "some-file.js")

    assert content is None

    return


# =============================================================================
# Unit Tests for content_type()
# =============================================================================

def test_content_type_returns_javascript_for_js():
    """
        Verify that content_type returns application/javascript for .js files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("swagger-ui-bundle.js")

    assert mime == "application/javascript"

    return


def test_content_type_returns_css_for_css():
    """
        Verify that content_type returns text/css for .css files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("swagger-ui.css")

    assert mime == "text/css"

    return


def test_content_type_returns_png_for_png():
    """
        Verify that content_type returns image/png for .png files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("favicon-32x32.png")

    assert mime == "image/png"

    return


def test_content_type_returns_svg_for_svg():
    """
        Verify that content_type returns image/svg+xml for .svg files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("icon.svg")

    assert mime == "image/svg+xml"

    return


def test_content_type_returns_ico_for_ico():
    """
        Verify that content_type returns image/x-icon for .ico files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("favicon.ico")

    assert mime == "image/x-icon"

    return


def test_content_type_returns_json_for_json():
    """
        Verify that content_type returns application/json for .json files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("manifest.json")

    assert mime == "application/json"

    return


def test_content_type_returns_woff_for_woff():
    """
        Verify that content_type returns font/woff for .woff files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("font.woff")

    assert mime == "font/woff"

    return


def test_content_type_returns_woff2_for_woff2():
    """
        Verify that content_type returns font/woff2 for .woff2 files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("font.woff2")

    assert mime == "font/woff2"

    return


def test_content_type_returns_ttf_for_ttf():
    """
        Verify that content_type returns font/ttf for .ttf files.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("font.ttf")

    assert mime == "font/ttf"

    return


def test_content_type_returns_octet_stream_for_unknown():
    """
        Verify that content_type returns application/octet-stream for
        unrecognized file extensions.
    """
    resolver = AssetResolver()

    mime = resolver.content_type("file.xyz")

    assert mime == "application/octet-stream"

    return


# =============================================================================
# Unit Tests for verify_integrity()
# =============================================================================

def test_verify_integrity_passes_for_unmodified_files():
    """
        Verify that verify_integrity returns an empty list when all
        vendored files match their manifest checksums.
    """
    resolver = AssetResolver()

    errors = resolver.verify_integrity()

    assert isinstance(errors, list)
    assert len(errors) == 0

    return


# =============================================================================
# Unit Tests for version properties
# =============================================================================

def test_swagger_ui_version_returns_version_string():
    """
        Verify that swagger_ui_version returns a non-None version string
        from the manifest.
    """
    resolver = AssetResolver()

    version = resolver.swagger_ui_version

    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0

    return


def test_redoc_version_returns_version_string():
    """
        Verify that redoc_version returns a non-None version string
        from the manifest.
    """
    resolver = AssetResolver()

    version = resolver.redoc_version

    assert version is not None
    assert isinstance(version, str)
    assert len(version) > 0

    return
