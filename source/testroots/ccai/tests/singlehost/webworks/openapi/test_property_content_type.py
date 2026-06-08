"""
    Property test for Content-Type correctness in the AssetResolver.

    This module verifies Property 4: Content-Type Correctness.

    For all supported file extensions, the MIME type mapping SHALL return
    the correct Content-Type value.

    **Validates: Requirements 8.8**
"""

from ccai.webworks.openapi.assets import AssetResolver


# =============================================================================
# Test Data: Extension to Expected MIME Type Mapping
# =============================================================================

# Each entry is (filename, expected_mime_type).
# We generate multiple filenames per extension to exercise the mapping
# with varied prefixes and casing patterns.

_CONTENT_TYPE_CASES = [
    # .js files
    ("swagger-ui-bundle.js", "application/javascript"),
    ("redoc.standalone.js", "application/javascript"),
    ("app.min.js", "application/javascript"),
    ("vendor.js", "application/javascript"),

    # .css files
    ("swagger-ui.css", "text/css"),
    ("styles.css", "text/css"),
    ("theme.min.css", "text/css"),

    # .png files
    ("favicon-32x32.png", "image/png"),
    ("logo.png", "image/png"),
    ("icon-16x16.png", "image/png"),

    # .svg files
    ("logo.svg", "image/svg+xml"),
    ("icon.svg", "image/svg+xml"),
    ("diagram.svg", "image/svg+xml"),

    # .ico files
    ("favicon.ico", "image/x-icon"),
    ("app.ico", "image/x-icon"),

    # .json files
    ("manifest.json", "application/json"),
    ("config.json", "application/json"),
    ("openapi.json", "application/json"),

    # .map files
    ("bundle.js.map", "application/json"),
    ("styles.css.map", "application/json"),

    # .woff files
    ("roboto.woff", "font/woff"),
    ("opensans.woff", "font/woff"),

    # .woff2 files
    ("roboto.woff2", "font/woff2"),
    ("opensans.woff2", "font/woff2"),

    # .ttf files
    ("roboto.ttf", "font/ttf"),
    ("opensans.ttf", "font/ttf"),

    # Unknown extensions should return application/octet-stream
    ("file.xyz", "application/octet-stream"),
    ("data.bin", "application/octet-stream"),
    ("archive.tar", "application/octet-stream"),
    ("readme.txt", "application/octet-stream"),
    ("image.bmp", "application/octet-stream"),
]


# =============================================================================
# Property Test
# =============================================================================

def test_property_content_type_correctness():
    """
        **Validates: Requirements 8.8**

        Property 4: Content-Type Correctness

        For all supported file extensions, verify the MIME type mapping
        returns the correct Content-Type.  This test iterates over a
        comprehensive set of filenames covering every supported extension
        and several unsupported extensions.
    """
    resolver = AssetResolver()

    total_cases = len(_CONTENT_TYPE_CASES)
    total_checks = 0

    for case_entry in _CONTENT_TYPE_CASES:
        filename = case_entry[0]
        expected_mime = case_entry[1]

        actual_mime = resolver.content_type(filename)

        if actual_mime != expected_mime:
            errmsg = (
                "Content-Type mismatch for '{}': "
                "expected='{}', actual='{}'"
            ).format(filename, expected_mime, actual_mime)
            raise AssertionError(errmsg)

        total_checks += 1

    # Verify we tested a meaningful number of cases
    if total_cases < 10:
        errmsg = "Expected at least 10 test cases, got {}".format(total_cases)
        raise AssertionError(errmsg)

    if total_checks < 10:
        errmsg = "Expected at least 10 checks, got {}".format(total_checks)
        raise AssertionError(errmsg)

    return
