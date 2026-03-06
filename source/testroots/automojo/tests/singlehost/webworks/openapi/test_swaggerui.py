"""
    Tests for the Swagger_UI_Blueprint class in the OpenAPI swaggerui module.

    This module contains unit tests covering the Swagger_UI_Blueprint class
    initialization, serve_ui endpoint, serve_spec endpoint, configuration
    options, HTML template rendering, and blueprint registration.
"""

import json

from automojo.testbase.mocking import Mock

from automojo.webworks.openapi.configuration import OpenAPIInfo
from automojo.webworks.openapi.swaggerui import (
    SWAGGER_UI_HTML_TEMPLATE,
    SwaggerUIBlueprint,
)


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
# Unit Tests for Swagger_UI_Blueprint Initialization
# =============================================================================

def test_swagger_ui_blueprint_default_initialization():
    """
        Test that Swagger_UI_Blueprint initializes with correct default values.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)

    if blueprint.ui_path != "/docs":
        errmsg = f"Expected ui_path '/docs', got {blueprint.ui_path!r}"
        raise AssertionError(errmsg)

    if blueprint.spec_path != "/openapi.json":
        errmsg = f"Expected spec_path '/openapi.json', got {blueprint.spec_path!r}"
        raise AssertionError(errmsg)

    if blueprint.static_path != "/_swagger":
        errmsg = f"Expected static_path '/_swagger', got {blueprint.static_path!r}"
        raise AssertionError(errmsg)

    if blueprint.try_it_out is not True:
        errmsg = f"Expected try_it_out True, got {blueprint.try_it_out!r}"
        raise AssertionError(errmsg)

    if blueprint.doc_expansion != "list":
        errmsg = f"Expected doc_expansion 'list', got {blueprint.doc_expansion!r}"
        raise AssertionError(errmsg)

    if blueprint.filter is not True:
        errmsg = f"Expected filter True, got {blueprint.filter!r}"
        raise AssertionError(errmsg)

    return


def test_swagger_ui_blueprint_custom_initialization():
    """
        Test that Swagger_UI_Blueprint accepts custom configuration values.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(
        generator=generator,
        ui_path="/api-docs",
        spec_path="/api/spec.json",
        try_it_out=False,
        doc_expansion="none",
        filter=False,
        deepLinking=True,
    )

    if blueprint.ui_path != "/api-docs":
        errmsg = f"Expected ui_path '/api-docs', got {blueprint.ui_path!r}"
        raise AssertionError(errmsg)

    if blueprint.spec_path != "/api/spec.json":
        errmsg = f"Expected spec_path '/api/spec.json', got {blueprint.spec_path!r}"
        raise AssertionError(errmsg)

    if blueprint.try_it_out is not False:
        errmsg = f"Expected try_it_out False, got {blueprint.try_it_out!r}"
        raise AssertionError(errmsg)

    if blueprint.doc_expansion != "none":
        errmsg = f"Expected doc_expansion 'none', got {blueprint.doc_expansion!r}"
        raise AssertionError(errmsg)

    if blueprint.filter is not False:
        errmsg = f"Expected filter False, got {blueprint.filter!r}"
        raise AssertionError(errmsg)

    if blueprint.swagger_config.get("deepLinking") is not True:
        errmsg = f"Expected swagger_config deepLinking True, got {blueprint.swagger_config!r}"
        raise AssertionError(errmsg)

    return


def test_swagger_ui_blueprint_stores_generator():
    """
        Test that the blueprint stores the generator reference.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)

    if blueprint.generator is not generator:
        errmsg = "Expected blueprint.generator to be the same object as the provided generator"
        raise AssertionError(errmsg)

    return


def test_swagger_ui_blueprint_base_path():
    """
        Test that the Swagger_UI_Blueprint class has the expected base_path.
    """
    if SwaggerUIBlueprint.base_path != "/docs":
        errmsg = f"Expected base_path '/docs', got {SwaggerUIBlueprint.base_path!r}"
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
    blueprint = SwaggerUIBlueprint(generator=generator)
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
    blueprint = SwaggerUIBlueprint(generator=generator)
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
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, _, headers = blueprint.serve_ui()

    if headers.get("Content-Type") != "text/html":
        errmsg = f"Expected Content-Type 'text/html', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_swagger_ui_div():
    """
        Test that the HTML output contains the swagger-ui div element.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if '<div id="swagger-ui"></div>' not in html:
        errmsg = "Expected HTML to contain '<div id=\"swagger-ui\"></div>'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_swagger_ui_bundle_script():
    """
        Test that the HTML output includes the Swagger UI bundle script
        referencing the local static path.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "/_swagger/swagger-ui-bundle.js" not in html:
        errmsg = "Expected HTML to contain '/_swagger/swagger-ui-bundle.js'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_swagger_ui_css():
    """
        Test that the HTML output includes the Swagger UI CSS link
        referencing the local static path.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "/_swagger/swagger-ui.css" not in html:
        errmsg = "Expected HTML to contain '/_swagger/swagger-ui.css'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_api_title():
    """
        Test that the HTML title includes the API title from the generator info.
    """
    generator = _create_mock_generator(title="My Custom API")
    blueprint = SwaggerUIBlueprint(generator=generator)
    html, _, _ = blueprint.serve_ui()

    if "My Custom API - Swagger UI" not in html:
        errmsg = "Expected HTML to contain 'My Custom API - Swagger UI'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_contains_spec_url():
    """
        Test that the HTML contains the configured spec URL.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, spec_path="/api/v1/spec.json")
    html, _, _ = blueprint.serve_ui()

    if '"/api/v1/spec.json"' not in html:
        errmsg = "Expected HTML to contain the spec URL '/api/v1/spec.json'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_try_it_out_enabled():
    """
        Test that tryItOutEnabled is set to true when try_it_out is True.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, try_it_out=True)
    html, _, _ = blueprint.serve_ui()

    if "tryItOutEnabled: true" not in html:
        errmsg = "Expected HTML to contain 'tryItOutEnabled: true'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_try_it_out_disabled():
    """
        Test that tryItOutEnabled is set to false when try_it_out is False.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, try_it_out=False)
    html, _, _ = blueprint.serve_ui()

    if "tryItOutEnabled: false" not in html:
        errmsg = "Expected HTML to contain 'tryItOutEnabled: false'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_doc_expansion_option():
    """
        Test that docExpansion is set to the configured value.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, doc_expansion="full")
    html, _, _ = blueprint.serve_ui()

    if 'docExpansion: "full"' not in html:
        errmsg = "Expected HTML to contain 'docExpansion: \"full\"'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_filter_enabled():
    """
        Test that filter is set to true when filter is True.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, filter=True)
    html, _, _ = blueprint.serve_ui()

    if "filter: true" not in html:
        errmsg = "Expected HTML to contain 'filter: true'"
        raise AssertionError(errmsg)

    return


def test_serve_ui_html_filter_disabled():
    """
        Test that filter is set to false when filter is False.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, filter=False)
    html, _, _ = blueprint.serve_ui()

    if "filter: false" not in html:
        errmsg = "Expected HTML to contain 'filter: false'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for serve_spec()
# =============================================================================

def test_serve_spec_returns_tuple_with_three_elements():
    """
        Test that serve_spec returns a tuple of (json, status_code, headers).
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    result = blueprint.serve_spec()

    if not isinstance(result, tuple):
        errmsg = f"Expected tuple, got {type(result).__name__}"
        raise AssertionError(errmsg)

    if len(result) != 3:
        errmsg = f"Expected tuple of length 3, got length {len(result)}"
        raise AssertionError(errmsg)

    return


def test_serve_spec_returns_status_200():
    """
        Test that serve_spec returns HTTP status code 200.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, status_code, _ = blueprint.serve_spec()

    if status_code != 200:
        errmsg = f"Expected status code 200, got {status_code}"
        raise AssertionError(errmsg)

    return


def test_serve_spec_returns_json_content_type():
    """
        Test that serve_spec returns Content-Type application/json in headers.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, _, headers = blueprint.serve_spec()

    if headers.get("Content-Type") != "application/json":
        errmsg = f"Expected Content-Type 'application/json', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_spec_returns_valid_json():
    """
        Test that serve_spec returns valid JSON content.
    """
    spec_dict = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {"/users": {"get": {"operationId": "list_users"}}},
    }
    generator = _create_mock_generator(spec_dict=spec_dict)
    blueprint = SwaggerUIBlueprint(generator=generator)
    json_content, _, _ = blueprint.serve_spec()

    parsed = json.loads(json_content)

    if parsed.get("openapi") != "3.0.3":
        errmsg = f"Expected openapi '3.0.3', got {parsed.get('openapi')!r}"
        raise AssertionError(errmsg)

    if parsed.get("info", {}).get("title") != "Test API":
        errmsg = f"Expected info.title 'Test API', got {parsed.get('info', {}).get('title')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_spec_uses_generator_generate_json():
    """
        Test that serve_spec calls generator.generate_json() to get the spec.
    """
    expected_json = '{"openapi": "3.0.3"}'
    generator = _create_mock_generator()
    ctx = generator.mock_context()
    ctx.mock_method("generate_json", return_value=expected_json)

    blueprint = SwaggerUIBlueprint(generator=generator)
    json_content, _, _ = blueprint.serve_spec()

    if json_content != expected_json:
        errmsg = f"Expected JSON content {expected_json!r}, got {json_content!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Configuration Options
# =============================================================================

def test_swagger_config_extra_options_in_html():
    """
        Test that extra swagger_config options appear in the generated HTML.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(
        generator=generator,
        deepLinking=True,
        displayRequestDuration=True,
    )
    html, _, _ = blueprint.serve_ui()

    if "deepLinking: true" not in html:
        errmsg = "Expected HTML to contain 'deepLinking: true'"
        raise AssertionError(errmsg)

    if "displayRequestDuration: true" not in html:
        errmsg = "Expected HTML to contain 'displayRequestDuration: true'"
        raise AssertionError(errmsg)

    return


def test_swagger_config_string_option_in_html():
    """
        Test that string-valued extra config options are quoted in the HTML.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(
        generator=generator,
        defaultModelRendering="model",
    )
    html, _, _ = blueprint.serve_ui()

    if 'defaultModelRendering: "model"' not in html:
        errmsg = "Expected HTML to contain 'defaultModelRendering: \"model\"'"
        raise AssertionError(errmsg)

    return


def test_swagger_config_numeric_option_in_html():
    """
        Test that numeric extra config options appear correctly in the HTML.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(
        generator=generator,
        maxDisplayedTags=10,
    )
    html, _, _ = blueprint.serve_ui()

    if "maxDisplayedTags: 10" not in html:
        errmsg = "Expected HTML to contain 'maxDisplayedTags: 10'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_descriptors()
# =============================================================================

def test_get_descriptors_returns_three_descriptors():
    """
        Test that get_descriptors returns exactly three endpoint descriptors
        (UI, spec, and static asset routes).
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    if len(descriptors) != 3:
        errmsg = f"Expected 3 descriptors, got {len(descriptors)}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_ui_descriptor_path():
    """
        Test that the UI descriptor has the configured ui_path.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, ui_path="/api-docs")
    descriptors = blueprint.get_descriptors()
    ui_descriptor = descriptors[0]

    if ui_descriptor.path != "/api-docs":
        errmsg = f"Expected UI descriptor path '/api-docs', got {ui_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_spec_descriptor_path():
    """
        Test that the spec descriptor has the configured spec_path.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, spec_path="/api/spec.json")
    descriptors = blueprint.get_descriptors()
    spec_descriptor = descriptors[1]

    if spec_descriptor.path != "/api/spec.json":
        errmsg = f"Expected spec descriptor path '/api/spec.json', got {spec_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_methods_are_get():
    """
        Test that both descriptors use the GET method.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    for descriptor in descriptors:
        if descriptor.methods != ["GET"]:
            errmsg = f"Expected methods ['GET'], got {descriptor.methods!r}"
            raise AssertionError(errmsg)

    return


def test_get_descriptors_ui_handler_is_serve_ui():
    """
        Test that the UI descriptor handler is the serve_ui bound method.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    ui_descriptor = descriptors[0]

    if ui_descriptor.handler.__func__ is not SwaggerUIBlueprint.serve_ui:
        errmsg = "Expected UI descriptor handler to be bound to Swagger_UI_Blueprint.serve_ui"
        raise AssertionError(errmsg)

    if ui_descriptor.handler.__self__ is not blueprint:
        errmsg = "Expected UI descriptor handler to be bound to the blueprint instance"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_spec_handler_is_serve_spec():
    """
        Test that the spec descriptor handler is the serve_spec bound method.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    spec_descriptor = descriptors[1]

    if spec_descriptor.handler.__func__ is not SwaggerUIBlueprint.serve_spec:
        errmsg = "Expected spec descriptor handler to be bound to Swagger_UI_Blueprint.serve_spec"
        raise AssertionError(errmsg)

    if spec_descriptor.handler.__self__ is not blueprint:
        errmsg = "Expected spec descriptor handler to be bound to the blueprint instance"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_have_documentation_tags():
    """
        Test that both descriptors have the 'documentation' tag.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    for descriptor in descriptors:
        if "documentation" not in descriptor.tags:
            errmsg = f"Expected 'documentation' in tags, got {descriptor.tags!r}"
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
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = SwaggerUIBlueprint.register(instance=blueprint)

    if len(descriptors) != 3:
        errmsg = f"Expected 3 descriptors, got {len(descriptors)}"
        raise AssertionError(errmsg)

    return


def test_register_with_router_adds_descriptors():
    """
        Test that register with a router calls add_endpoint for each descriptor.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)

    mock_router = Mock()
    mock_router.configure(recursive=True)

    added_descriptors = []

    def capture_add_endpoint(descriptor):
        added_descriptors.append(descriptor)

    mock_router.mock_context().mock_method("add_endpoint", side_effect=capture_add_endpoint)

    SwaggerUIBlueprint.register(router=mock_router, instance=blueprint)

    if len(added_descriptors) != 3:
        errmsg = f"Expected 3 descriptors added to router, got {len(added_descriptors)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HTML Template
# =============================================================================

def test_html_template_is_valid_html():
    """
        Test that the SWAGGER_UI_HTML_TEMPLATE contains valid HTML structure.
    """
    if "<!DOCTYPE html>" not in SWAGGER_UI_HTML_TEMPLATE:
        errmsg = "Expected template to contain '<!DOCTYPE html>'"
        raise AssertionError(errmsg)

    if "<html" not in SWAGGER_UI_HTML_TEMPLATE:
        errmsg = "Expected template to contain '<html'"
        raise AssertionError(errmsg)

    if "</html>" not in SWAGGER_UI_HTML_TEMPLATE:
        errmsg = "Expected template to contain '</html>'"
        raise AssertionError(errmsg)

    return


def test_html_template_contains_local_swagger_ui_bundle():
    """
        Test that the template references the Swagger UI bundle via local static_path.
    """
    if "{static_path}/swagger-ui-bundle.js" not in SWAGGER_UI_HTML_TEMPLATE:
        errmsg = "Expected template to reference swagger-ui-bundle.js via local static_path"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for static_path and AssetResolver integration
# =============================================================================

def test_swagger_ui_blueprint_default_static_path():
    """
        Test that the default static_path is '/_swagger'.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)

    if blueprint.static_path != "/_swagger":
        errmsg = f"Expected static_path '/_swagger', got {blueprint.static_path!r}"
        raise AssertionError(errmsg)

    return


def test_swagger_ui_blueprint_custom_static_path():
    """
        Test that a custom static_path is stored correctly.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, static_path="/assets/swagger")

    if blueprint.static_path != "/assets/swagger":
        errmsg = f"Expected static_path '/assets/swagger', got {blueprint.static_path!r}"
        raise AssertionError(errmsg)

    return


def test_swagger_ui_blueprint_has_asset_resolver():
    """
        Test that the blueprint creates an AssetResolver instance internally.
    """
    from automojo.webworks.openapi.assets import AssetResolver

    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)

    if not isinstance(blueprint._asset_resolver, AssetResolver):
        errmsg = f"Expected _asset_resolver to be AssetResolver, got {type(blueprint._asset_resolver).__name__}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for _build_swagger_html local asset references
# =============================================================================

def test_build_swagger_html_no_cdn_references():
    """
        Test that _build_swagger_html output contains no external CDN references.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    html = blueprint._build_swagger_html()

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


def test_build_swagger_html_references_local_js():
    """
        Test that _build_swagger_html references static_path for JS.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, static_path="/my-assets")
    html = blueprint._build_swagger_html()

    if "/my-assets/swagger-ui-bundle.js" not in html:
        errmsg = "Expected HTML to reference '/my-assets/swagger-ui-bundle.js'"
        raise AssertionError(errmsg)

    return


def test_build_swagger_html_references_local_css():
    """
        Test that _build_swagger_html references static_path for CSS.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, static_path="/my-assets")
    html = blueprint._build_swagger_html()

    if "/my-assets/swagger-ui.css" not in html:
        errmsg = "Expected HTML to reference '/my-assets/swagger-ui.css'"
        raise AssertionError(errmsg)

    return


def test_build_swagger_html_references_local_favicon():
    """
        Test that _build_swagger_html includes a favicon link referencing
        the local static_path.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    html = blueprint._build_swagger_html()

    if "/_swagger/favicon-32x32.png" not in html:
        errmsg = "Expected HTML to reference '/_swagger/favicon-32x32.png'"
        raise AssertionError(errmsg)

    return


def test_build_swagger_html_no_standalone_preset():
    """
        Test that _build_swagger_html does not reference
        SwaggerUIStandalonePreset or StandaloneLayout.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    html = blueprint._build_swagger_html()

    if "SwaggerUIStandalonePreset" in html:
        errmsg = "HTML should not contain 'SwaggerUIStandalonePreset'"
        raise AssertionError(errmsg)

    if "StandaloneLayout" in html:
        errmsg = "HTML should not contain 'StandaloneLayout'"
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
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, status_code, headers = blueprint.serve_static("swagger-ui-bundle.js")

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "application/javascript":
        errmsg = f"Expected Content-Type 'application/javascript', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_static_returns_correct_content_type_for_css():
    """
        Test that serve_static returns text/css for .css files.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, status_code, headers = blueprint.serve_static("swagger-ui.css")

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "text/css":
        errmsg = f"Expected Content-Type 'text/css', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_static_returns_correct_content_type_for_png():
    """
        Test that serve_static returns image/png for .png files.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, status_code, headers = blueprint.serve_static("favicon-32x32.png")

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if headers.get("Content-Type") != "image/png":
        errmsg = f"Expected Content-Type 'image/png', got {headers.get('Content-Type')!r}"
        raise AssertionError(errmsg)

    return


def test_serve_static_returns_cache_control_header():
    """
        Test that serve_static sets Cache-Control for immutable caching.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    _, status_code, headers = blueprint.serve_static("swagger-ui-bundle.js")

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
    blueprint = SwaggerUIBlueprint(generator=generator)
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
    blueprint = SwaggerUIBlueprint(generator=generator)
    content, status_code, _ = blueprint.serve_static("swagger-ui-bundle.js")

    if status_code != 200:
        errmsg = f"Expected status 200, got {status_code}"
        raise AssertionError(errmsg)

    if not isinstance(content, bytes):
        errmsg = f"Expected bytes content, got {type(content).__name__}"
        raise AssertionError(errmsg)

    if len(content) == 0:
        errmsg = "Expected non-empty content for swagger-ui-bundle.js"
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
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()

    static_descriptor = descriptors[2]

    if "/_swagger/<filename>" != static_descriptor.path:
        errmsg = f"Expected static descriptor path '/_swagger/<filename>', got {static_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_static_route_uses_custom_path():
    """
        Test that the static route descriptor uses the configured static_path.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator, static_path="/custom-static")
    descriptors = blueprint.get_descriptors()

    static_descriptor = descriptors[2]

    if "/custom-static/<filename>" != static_descriptor.path:
        errmsg = f"Expected path '/custom-static/<filename>', got {static_descriptor.path!r}"
        raise AssertionError(errmsg)

    return


def test_get_descriptors_static_handler_is_serve_static():
    """
        Test that the static descriptor handler is the serve_static bound method.
    """
    generator = _create_mock_generator()
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    static_descriptor = descriptors[2]

    if static_descriptor.handler.__func__ is not SwaggerUIBlueprint.serve_static:
        errmsg = "Expected static descriptor handler to be bound to SwaggerUIBlueprint.serve_static"
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
    blueprint = SwaggerUIBlueprint(generator=generator)
    descriptors = blueprint.get_descriptors()
    static_descriptor = descriptors[2]

    if static_descriptor.methods != ["GET"]:
        errmsg = f"Expected methods ['GET'], got {static_descriptor.methods!r}"
        raise AssertionError(errmsg)

    return
