"""
    Tests for the ReDoc_Blueprint class in the OpenAPI redoc module.

    This module contains unit tests covering the ReDoc_Blueprint class
    initialization, serve_ui endpoint, configuration options, HTML template
    rendering, blueprint registration, and simultaneous hosting with
    Swagger UI.
"""

import json

from automojo.testbase.mocking import Mock

from automojo.webworks.openapi.configuration import OpenAPIInfo
from automojo.webworks.openapi.redoc import (
    REDOC_HTML_TEMPLATE,
    ReDocBlueprint,
)
from automojo.webworks.openapi.swaggerui import SwaggerUIBlueprint


# =============================================================================
# Helper Functions
# =============================================================================

def _create_mock_generator(title="Test API", version="1.0.0", spec_dict=None):
    """
        Create a mock OpenAPI_Generator with configurable info and spec output.

        :param title: The API title for the info object.
        :param version: The API version for the info object.
        :param spec_dict: The specification dictionary returned by generate().

        :returns: A configured Mock object acting as an OpenAPI_Generator.
    """
    mock_generator = Mock()
    mock_generator.configure(recursive=True)

    info = OpenAPIInfo(title=title, version=version)
    ctx = mock_generator.mock_context()
    ctx.set_attribute("info", info)

    if spec_dict is None:
        spec_dict = {
            "openapi": "3.0.3",
            "info": {"title": title, "version": version},
            "paths": {},
        }

    json_output = json.dumps(spec_dict, indent=2, sort_keys=True)
    ctx.mock_method("generate_json", return_value=json_output)

    return mock_generator


# =============================================================================
# Unit Tests for ReDoc_Blueprint Initialization
# =============================================================================

def test_redoc_blueprint_default_initialization():
    """
        Test that ReDoc_Blueprint initializes with correct default values.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)

    if blueprint.ui_path != "/redoc":
        errmsg = f"Expected ui_path '/redoc', got {blueprint.ui_path!r}"
        raise AssertionError(errmsg)

    if blueprint.spec_url != "/openapi.json":
        errmsg = f"Expected spec_url '/openapi.json', got {blueprint.spec_url!r}"
        raise AssertionError(errmsg)

    if blueprint.static_path != "/_redoc":
        errmsg = f"Expected static_path '/_redoc', got {blueprint.static_path!r}"
        raise AssertionError(errmsg)

    if blueprint.redoc_config != {}:
        errmsg = f"Expected empty redoc_config, got {blueprint.redoc_config!r}"
        raise AssertionError(errmsg)

    return


def test_redoc_blueprint_custom_initialization():
    """
        Test that ReDoc_Blueprint accepts custom configuration values.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(
        generator=generator,
        ui_path="/api-redoc",
        spec_url="/api/v1/spec.json",
        hideDownloadButton=True,
        expandResponses="200,201",
    )

    if blueprint.ui_path != "/api-redoc":
        errmsg = f"Expected ui_path '/api-redoc', got {blueprint.ui_path!r}"
        raise AssertionError(errmsg)

    if blueprint.spec_url != "/api/v1/spec.json":
        errmsg = f"Expected spec_url '/api/v1/spec.json', got {blueprint.spec_url!r}"
        raise AssertionError(errmsg)

    if blueprint.redoc_config.get("hideDownloadButton") is not True:
        errmsg = f"Expected hideDownloadButton True, got {blueprint.redoc_config!r}"
        raise AssertionError(errmsg)

    if blueprint.redoc_config.get("expandResponses") != "200,201":
        errmsg = f"Expected expandResponses '200,201', got {blueprint.redoc_config!r}"
        raise AssertionError(errmsg)

    return


def test_redoc_blueprint_stores_generator():
    """
        Test that the blueprint stores the generator reference.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)

    if blueprint.generator is not generator:
        errmsg = "Expected blueprint.generator to be the same object as the provided generator"
        raise AssertionError(errmsg)

    return


def test_redoc_blueprint_base_path():
    """
        Test that the ReDoc_Blueprint class has the expected base_path.
    """
    if ReDocBlueprint.base_path != "/redoc":
        errmsg = f"Expected base_path '/redoc', got {ReDocBlueprint.base_path!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for serve_ui()
# =============================================================================

def test_serve_ui_returns_tuple_with_three_elements():
    """
        Test that serve_ui returns a tuple of (html, status_code, headers).
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    result = blueprint.serve_ui()

    if not isinstance(result, tuple):
        errmsg = f"Expected tuple, got {type(result).__name__}"
        raise AssertionError(errmsg)

    if len(result) != 3:
        errmsg = f"Expected tuple of length 3, got length {len(result)}"
        raise AssertionError(errmsg)

    return


def test_serve_ui_returns_status_200():
    """
        Test that serve_ui returns HTTP status code 200.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    _, status_code, _ = blueprint.serve_ui()

    if status_code != 200:
        errmsg = f"Expected status code 200, got {status_code}"
        raise AssertionError(errmsg)

    return


def test_serve_ui_returns_html_content_type():
    """
        Test that serve_ui returns Content-Type text/html in headers.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    _, _, headers = blueprint.serve_ui()

    if headers.get("Content-Type") != "text/html":
        errmsg = f"Expected Content-Type 'text/html', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_redoc_element():
    """
        Test that the HTML output contains the redoc custom element.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "<redoc " not in html:
        errmsg = "Expected HTML to contain '<redoc ' element"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_redoc_script():
    """
        Test that the HTML output includes the ReDoc standalone script tag.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "redoc.standalone.js" not in html:
        errmsg = "Expected HTML to contain 'redoc.standalone.js'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_api_title():
    """
        Test that the HTML title includes the API title from the generator info.
    """
    generator = _create_mock_generator(title="My Custom API")
    blueprint = ReDocBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "My Custom API - API Documentation" not in html:
        errmsg = "Expected HTML to contain 'My Custom API - API Documentation'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_spec_url():
    """
        Test that the HTML contains the configured spec URL in the redoc element.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator, spec_url="/api/v1/spec.json")
    html, _, _ = blueprint.serve_ui()

    if 'spec-url="/api/v1/spec.json"' not in html:
        errmsg = "Expected HTML to contain 'spec-url=\"/api/v1/spec.json\"'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_default_spec_url():
    """
        Test that the HTML contains the default spec URL when none is specified.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if 'spec-url="/openapi.json"' not in html:
        errmsg = "Expected HTML to contain 'spec-url=\"/openapi.json\"'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Configuration Options
# =============================================================================

def test_redoc_config_boolean_option_in_html():
    """
        Test that boolean ReDoc config options appear as attributes in the HTML.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(
        generator=generator,
        hideDownloadButton=True,
    )
    html, _, _ = blueprint.serve_ui()

    if 'hideDownloadButton="true"' not in html:
        errmsg = "Expected HTML to contain 'hideDownloadButton=\"true\"'"
        raise AssertionError(errmsg)

    return


def test_redoc_config_boolean_false_option_in_html():
    """
        Test that boolean false ReDoc config options render correctly.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(
        generator=generator,
        hideDownloadButton=False,
    )
    html, _, _ = blueprint.serve_ui()

    if 'hideDownloadButton="false"' not in html:
        errmsg = "Expected HTML to contain 'hideDownloadButton=\"false\"'"
        raise AssertionError(errmsg)

    return


def test_redoc_config_string_option_in_html():
    """
        Test that string-valued ReDoc config options appear as attributes.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(
        generator=generator,
        expandResponses="200,201",
    )
    html, _, _ = blueprint.serve_ui()

    if 'expandResponses="200,201"' not in html:
        errmsg = "Expected HTML to contain 'expandResponses=\"200,201\"'"
        raise AssertionError(errmsg)

    return


def test_redoc_config_multiple_options_in_html():
    """
        Test that multiple ReDoc config options all appear in the HTML.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(
        generator=generator,
        hideDownloadButton=True,
        expandResponses="all",
        requiredPropsFirst=True,
    )
    html, _, _ = blueprint.serve_ui()

    if 'hideDownloadButton="true"' not in html:
        errmsg = "Expected HTML to contain 'hideDownloadButton=\"true\"'"
        raise AssertionError(errmsg)

    if 'expandResponses="all"' not in html:
        errmsg = "Expected HTML to contain 'expandResponses=\"all\"'"
        raise AssertionError(errmsg)

    if 'requiredPropsFirst="true"' not in html:
        errmsg = "Expected HTML to contain 'requiredPropsFirst=\"true\"'"
        raise AssertionError(errmsg)

    return


def test_redoc_config_no_options_produces_clean_html():
    """
        Test that no config options produces a clean redoc element.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "<redoc spec-url=" not in html:
        errmsg = "Expected HTML to contain '<redoc spec-url='"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_descriptors()
# =============================================================================

def test_get_descriptors_returns_two_descriptors():
    """
        Test that get_descriptors returns exactly two endpoint descriptors.
        ReDoc has a UI endpoint and a static asset endpoint.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    if len(descriptors) != 2:
        errmsg = f"Expected 2 descriptors, got {len(descriptors)}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_ui_descriptor_path():
    """
        Test that the UI descriptor has the configured ui_path.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator, ui_path="/api-redoc")
    descriptors = blueprint.get_descriptors()
    ui_descriptor = descriptors[0]

    if ui_descriptor.path != "/api-redoc":
        errmsg = f"Expected UI descriptor path '/api-redoc', got {ui_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_default_path():
    """
        Test that the UI descriptor uses the default /redoc path.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    ui_descriptor = descriptors[0]

    if ui_descriptor.path != "/redoc":
        errmsg = f"Expected UI descriptor path '/redoc', got {ui_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_method_is_get():
    """
        Test that the descriptor uses the GET method.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    if descriptors[0].methods != ["GET"]:
        errmsg = f"Expected methods ['GET'], got {descriptors[0].methods!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_handler_is_serve_ui():
    """
        Test that the descriptor handler is the serve_ui bound method.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    ui_descriptor = descriptors[0]

    if ui_descriptor.handler.__func__ is not ReDocBlueprint.serve_ui:
        errmsg = "Expected descriptor handler to be bound to ReDoc_Blueprint.serve_ui"
        raise AssertionError(errmsg)

    if ui_descriptor.handler.__self__ is not blueprint:
        errmsg = "Expected descriptor handler to be bound to the blueprint instance"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_have_documentation_tag():
    """
        Test that the descriptor has the 'documentation' tag.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    if "documentation" not in descriptors[0].tags:
        errmsg = f"Expected 'documentation' in tags, got {descriptors[0].tags!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for register()
# =============================================================================

def test_register_with_instance_returns_descriptors():
    """
        Test that register with an instance returns the blueprint descriptors.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = ReDocBlueprint.register(instance=blueprint)

    if len(descriptors) != 2:
        errmsg = f"Expected 2 descriptors, got {len(descriptors)}"
        raise AssertionError(errmsg)

    return


def test_register_with_router_adds_descriptors():
    """
        Test that register with a router calls add_endpoint for each descriptor.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)

    mock_router = Mock()
    mock_router.configure(recursive=True)

    added_descriptors = []

    def capture_add_endpoint(descriptor):
        added_descriptors.append(descriptor)

    mock_router.mock_context().mock_method("add_endpoint", side_effect=capture_add_endpoint)

    ReDocBlueprint.register(router=mock_router, instance=blueprint)

    if len(added_descriptors) != 2:
        errmsg = f"Expected 2 descriptors added to router, got {len(added_descriptors)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HTML Template
# =============================================================================

def test_html_template_is_valid_html():
    """
        Test that the REDOC_HTML_TEMPLATE contains valid HTML structure.
    """
    if "<!DOCTYPE html>" not in REDOC_HTML_TEMPLATE:
        errmsg = "Expected template to contain '<!DOCTYPE html>'"
        raise AssertionError(errmsg)

    if "<html" not in REDOC_HTML_TEMPLATE:
        errmsg = "Expected template to contain '<html'"
        raise AssertionError(errmsg)

    if "</html>" not in REDOC_HTML_TEMPLATE:
        errmsg = "Expected template to contain '</html>'"
        raise AssertionError(errmsg)

    return


def test_html_template_contains_redoc_script():
    """
        Test that the template references the ReDoc standalone script via
        local static_path placeholder.
    """
    if "{static_path}/redoc.standalone.js" not in REDOC_HTML_TEMPLATE:
        errmsg = "Expected template to reference redoc.standalone.js via local static_path"
        raise AssertionError(errmsg)

    return


def test_html_template_no_google_fonts():
    """
        Test that the template does not include the Google Fonts CDN link.
    """
    if "fonts.googleapis.com" in REDOC_HTML_TEMPLATE:
        errmsg = "Template should not reference Google Fonts CDN"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for static_path and AssetResolver integration
# =============================================================================

def test_redoc_blueprint_default_static_path():
    """
        Test that the default static_path is '/_redoc'.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)

    if blueprint.static_path != "/_redoc":
        errmsg = f"Expected static_path '/_redoc', got {blueprint.static_path!r}"
        raise AssertionError(errmsg)

    return


def test_redoc_blueprint_custom_static_path():
    """
        Test that a custom static_path is stored correctly.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator, static_path="/assets/redoc")

    if blueprint.static_path != "/assets/redoc":
        errmsg = f"Expected static_path '/assets/redoc', got {blueprint.static_path!r}"
        raise AssertionError(errmsg)

    return


def test_redoc_blueprint_has_asset_resolver():
    """
        Test that the blueprint creates an AssetResolver instance internally.
    """
    from automojo.webworks.openapi.assets import AssetResolver

    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)

    if not isinstance(blueprint._asset_resolver, AssetResolver):
        errmsg = f"Expected _asset_resolver to be AssetResolver, got {type(blueprint._asset_resolver).__name__}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for _build_redoc_html local asset references
# =============================================================================

def test_build_redoc_html_no_cdn_references():
    """
        Test that _build_redoc_html output contains no external CDN references.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    html = blueprint._build_redoc_html()

    cdn_indicators = [
        "unpkg.com",
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com",
        "cdn.redoc.ly",
        "fonts.googleapis.com",
    ]

    for indicator in cdn_indicators:
        if indicator in html:
            errmsg = f"HTML should not contain CDN reference '{indicator}'"
            raise AssertionError(errmsg)

    return


def test_build_redoc_html_references_local_js():
    """
        Test that _build_redoc_html references static_path for JS.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator, static_path="/my-redoc-assets")
    html = blueprint._build_redoc_html()

    if "/my-redoc-assets/redoc.standalone.js" not in html:
        errmsg = "Expected HTML to reference '/my-redoc-assets/redoc.standalone.js'"
        raise AssertionError(errmsg)

    return


def test_build_redoc_html_default_static_path_js():
    """
        Test that _build_redoc_html references the default static_path for JS.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    html = blueprint._build_redoc_html()

    if "/_redoc/redoc.standalone.js" not in html:
        errmsg = "Expected HTML to reference '/_redoc/redoc.standalone.js'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for serve_static()
# =============================================================================

def test_serve_static_returns_correct_content_type_for_js():
    """
        Test that serve_static returns application/javascript for .js files.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    _, status_code, headers = blueprint.serve_static("redoc.standalone.js")

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "application/javascript":
        errmsg = f"Expected Content-Type 'application/javascript', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_static_returns_cache_control_header():
    """
        Test that serve_static sets Cache-Control for immutable caching.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    _, status_code, headers = blueprint.serve_static("redoc.standalone.js")

    expected_cache = "public, max-age=31536000, immutable"

    if headers.get("Cache-Control") != expected_cache:
        errmsg = f"Expected Cache-Control '{expected_cache}', got {headers.get('Cache-Control')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_static_returns_404_for_nonexistent_file():
    """
        Test that serve_static returns 404 for a file that does not exist.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    _, status_code, _ = blueprint.serve_static("nonexistent-file.js")

    if status_code != 404:
        errmsg = f"Expected status 404, got {status_code}"
        raise AssertionError(errmsg)

    return


def test_serve_static_returns_bytes_content():
    """
        Test that serve_static returns bytes content for existing files.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    content, status_code, _ = blueprint.serve_static("redoc.standalone.js")

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if not isinstance(content, bytes):
        errmsg = f"Expected bytes content, got {type(content).__name__}"
        raise AssertionError(errmsg)

    if len(content) == 0:
        errmsg = "Expected non-empty content for redoc.standalone.js"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_descriptors() with static route
# =============================================================================

def test_get_descriptors_includes_static_route():
    """
        Test that get_descriptors includes a static asset route descriptor.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    static_descriptor = descriptors[1]

    if "/_redoc/<filename>" != static_descriptor.path:
        errmsg = f"Expected static descriptor path '/_redoc/<filename>', got {static_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_static_route_uses_custom_path():
    """
        Test that the static route descriptor uses the configured static_path.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator, static_path="/custom-redoc-static")
    descriptors = blueprint.get_descriptors()

    static_descriptor = descriptors[1]

    if "/custom-redoc-static/<filename>" != static_descriptor.path:
        errmsg = f"Expected path '/custom-redoc-static/<filename>', got {static_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_static_handler_is_serve_static():
    """
        Test that the static descriptor handler is the serve_static bound method.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    static_descriptor = descriptors[1]

    if static_descriptor.handler.__func__ is not ReDocBlueprint.serve_static:
        errmsg = "Expected static descriptor handler to be bound to ReDocBlueprint.serve_static"
        raise AssertionError(errmsg)

    if static_descriptor.handler.__self__ is not blueprint:
        errmsg = "Expected static descriptor handler to be bound to the blueprint instance"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_static_route_is_get():
    """
        Test that the static route descriptor uses the GET method.
    """
    generator = _create_mock_generator()
    blueprint = ReDocBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    static_descriptor = descriptors[1]

    if static_descriptor.methods != ["GET"]:
        errmsg = f"Expected methods ['GET'], got {static_descriptor.methods!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Simultaneous Hosting
# =============================================================================

def test_simultaneous_hosting_both_blueprints_share_generator():
    """
        Test that Swagger UI and ReDoc can share the same generator instance.
    """
    generator = _create_mock_generator(title="Shared API")

    swagger_blueprint = SwaggerUIBlueprint(generator=generator)
    redoc_blueprint = ReDocBlueprint(generator=generator)

    if swagger_blueprint.generator is not redoc_blueprint.generator:
        errmsg = "Expected both blueprints to share the same generator instance"
        raise AssertionError(errmsg)

    return


def test_simultaneous_hosting_different_paths():
    """
        Test that Swagger UI and ReDoc serve on different default paths.
    """
    generator = _create_mock_generator()

    swagger_blueprint = SwaggerUIBlueprint(generator=generator)
    redoc_blueprint = ReDocBlueprint(generator=generator)

    if swagger_blueprint.ui_path == redoc_blueprint.ui_path:
        errmsg = (
            f"Expected different UI paths, both are {swagger_blueprint.ui_path!r}"
        )
        raise AssertionError(errmsg)

    return


def test_simultaneous_hosting_redoc_points_to_swagger_spec():
    """
        Test that ReDoc can point to the spec URL served by Swagger UI.
    """
    generator = _create_mock_generator()

    swagger_blueprint = SwaggerUIBlueprint(
        generator=generator,
        spec_path="/openapi.json",
    )
    redoc_blueprint = ReDocBlueprint(
        generator=generator,
        spec_url=swagger_blueprint.spec_path,
    )

    if redoc_blueprint.spec_url != swagger_blueprint.spec_path:
        errmsg = (
            f"Expected ReDoc spec_url '{swagger_blueprint.spec_path}', "
            f"got {redoc_blueprint.spec_url!r}"
        )
        raise AssertionError(errmsg)

    return


def test_simultaneous_hosting_both_serve_html():
    """
        Test that both blueprints produce valid HTML responses simultaneously.
    """
    generator = _create_mock_generator(title="Dual UI API")

    swagger_blueprint = SwaggerUIBlueprint(generator=generator)
    redoc_blueprint = ReDocBlueprint(generator=generator)

    swagger_html, swagger_status, swagger_headers = swagger_blueprint.serve_ui()
    redoc_html, redoc_status, redoc_headers = redoc_blueprint.serve_ui()

    if swagger_status != 200:
        errmsg = f"Expected Swagger UI status 200, got {swagger_status}"
        raise AssertionError(errmsg)

    if redoc_status != 200:
        errmsg = f"Expected ReDoc status 200, got {redoc_status}"
        raise AssertionError(errmsg)

    if swagger_headers.get("Content-Type") != "text/html":
        errmsg = "Expected Swagger UI Content-Type 'text/html'"
        raise AssertionError(errmsg)

    if redoc_headers.get("Content-Type") != "text/html":
        errmsg = "Expected ReDoc Content-Type 'text/html'"
        raise AssertionError(errmsg)

    if "swagger-ui" not in swagger_html:
        errmsg = "Expected Swagger UI HTML to contain 'swagger-ui'"
        raise AssertionError(errmsg)

    if "redoc" not in redoc_html.lower():
        errmsg = "Expected ReDoc HTML to contain 'redoc'"
        raise AssertionError(errmsg)

    return


def test_simultaneous_hosting_descriptors_do_not_overlap():
    """
        Test that descriptors from both blueprints have non-overlapping paths.
    """
    generator = _create_mock_generator()

    swagger_blueprint = SwaggerUIBlueprint(generator=generator)
    redoc_blueprint = ReDocBlueprint(generator=generator)

    swagger_descriptors = swagger_blueprint.get_descriptors()
    redoc_descriptors = redoc_blueprint.get_descriptors()

    swagger_paths = {d.path for d in swagger_descriptors}
    redoc_paths = {d.path for d in redoc_descriptors}

    overlap = swagger_paths & redoc_paths
    if overlap:
        errmsg = f"Expected no overlapping paths, found: {overlap}"
        raise AssertionError(errmsg)

    return
