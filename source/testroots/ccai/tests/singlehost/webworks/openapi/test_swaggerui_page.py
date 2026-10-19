"""
    Tests for the Swagger UI page, starter script and asset helpers.

    A page whose Content-Security-Policy allows scripts from its own origin only cannot hold an inline starter, so the page and the
    starter script are separate files, the options are explicit, and only the vendored Swagger UI files are ever handed out.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import json
import re

from ccai import testbase

from ccai.webworks.openapi.swaggerui import (
    SWAGGER_UI_ASSET_NAMES,
    SWAGGER_UI_INITIALIZER_NAME,
    SwaggerUIOptions,
    build_swagger_ui_config,
    read_swagger_ui_asset,
    render_swagger_ui_initializer,
    render_swagger_ui_page,
)


def test_the_page_loads_the_library_and_the_starter_from_the_asset_path_and_holds_no_script_of_its_own():
    """
        **Feature: Swagger UI page**
        **Property: the page has the Swagger UI container and two ``<script src>`` elements (the library and the starter) under the asset path, no script body,
        and no address on another host.**
    """
    page = render_swagger_ui_page(title="Demo API", static_path="/docs/assets")
    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", page, re.S)
    testbase.assert_equal(
        (
            'id="swagger-ui"' in page, [attributes.strip() for attributes, _body in scripts], [body.strip() for _attributes, body in scripts],
            "http://" in page or "https://" in page, "<title>Demo API - Swagger UI</title>" in page,
        ),
        (
            True, ['src="/docs/assets/swagger-ui-bundle.js"', 'src="/docs/assets/{}"'.format(SWAGGER_UI_INITIALIZER_NAME)], ["", ""],
            False, True,
        ),
    )
    return


def test_the_page_escapes_the_title_and_paths_it_is_given():
    """
        **Feature: Swagger UI page**
        **Property: markup in the title or in the asset path is escaped, never written into the page as markup.**
    """
    page = render_swagger_ui_page(title="<script>alert(1)</script>", static_path='/a"b')
    testbase.assert_equal(("<script>alert" in page, "&lt;script&gt;alert(1)&lt;/script&gt;" in page, '"/a"b/' in page), (False, True, False))
    return


def test_the_default_options_start_folded_with_deep_links_a_filter_and_the_schemas_block_hidden():
    """
        **Feature: Swagger UI page**
        **Property: the default configuration folds everything (``docExpansion: none``), keeps the open item in the address, shows the filter, hides the Schemas
        block, sorts groups and operations by name and leaves Try it out for a person to switch on.**
    """
    config = build_swagger_ui_config(spec_url="/openapi.json")
    testbase.assert_equal(
        config,
        {
            "url": "/openapi.json", "dom_id": "#swagger-ui", "tryItOutEnabled": False, "docExpansion": "none", "filter": True, "deepLinking": True,
            "defaultModelsExpandDepth": -1, "operationsSorter": "alpha", "tagsSorter": "alpha",
        },
    )
    return


def test_try_it_out_can_be_limited_to_get_or_removed():
    """
        **Feature: Swagger UI page**
        **Property: ``supported_submit_methods`` of ``("GET",)`` becomes ``["get"]`` (a page safe to leave open on a production system), ``()`` becomes ``[]`` (no Try
        it out), and ``None`` leaves the setting out so every method is allowed.**
    """
    get_only = build_swagger_ui_config(spec_url="/o.json", options=SwaggerUIOptions(supported_submit_methods=("GET",)))
    none = build_swagger_ui_config(spec_url="/o.json", options=SwaggerUIOptions(supported_submit_methods=()))
    everything = build_swagger_ui_config(spec_url="/o.json", options=SwaggerUIOptions(supported_submit_methods=None))
    testbase.assert_equal(
        (get_only["supportedSubmitMethods"], none["supportedSubmitMethods"], "supportedSubmitMethods" in everything),
        (["get"], [], False),
    )
    return


def test_a_doc_expansion_swagger_ui_does_not_know_is_refused():
    """
        **Feature: Swagger UI page**
        **Property: ``doc_expansion`` other than none, list or full raises ValueError naming the choices, rather than producing a page that silently ignores it.**
    """
    message = ""
    try:
        build_swagger_ui_config(spec_url="/o.json", options=SwaggerUIOptions(doc_expansion="open"))
    except ValueError as xcpt:
        message = str(xcpt)
    testbase.assert_equal(("none, list, full" in message, "'open'" in message), (True, True))
    return


def test_extra_settings_win_over_the_options():
    """
        **Feature: Swagger UI page**
        **Property: a setting given in ``extra`` replaces the one the options produced, so a page can use any Swagger UI setting this module does not name.**
    """
    config = build_swagger_ui_config(spec_url="/o.json", options=SwaggerUIOptions(), extra={"docExpansion": "list", "displayRequestDuration": True})
    testbase.assert_equal((config["docExpansion"], config["displayRequestDuration"]), ("list", True))
    return


def test_the_starter_script_starts_swagger_ui_with_the_configuration_and_the_apis_preset():
    """
        **Feature: Swagger UI page**
        **Property: the starter script defines the configuration as JSON, adds the ``apis`` preset (code, so not part of the JSON) and starts ``SwaggerUIBundle``;
        the JSON it holds is exactly the configuration built for the same arguments.**
    """
    script = render_swagger_ui_initializer(spec_url="/api/v1/_meta/openapi.json?group_by=path", options=SwaggerUIOptions(supported_submit_methods=("GET",)))
    match = re.search(r"var config = (\{.*?\n    \});", script, re.S)
    found = json.loads(match.group(1))
    testbase.assert_equal(
        (found, "config.presets = [SwaggerUIBundle.presets.apis];" in script, "window.ui = SwaggerUIBundle(config);" in script),
        (build_swagger_ui_config(spec_url="/api/v1/_meta/openapi.json?group_by=path", options=SwaggerUIOptions(supported_submit_methods=("GET",))), True, True),
    )
    return


def test_the_vendored_library_files_are_handed_out_with_their_content_types():
    """
        **Feature: Swagger UI page**
        **Property: the Swagger UI script, style and icon are returned with application/javascript, text/css and image/png, and the script is the real library (hundreds of kilobytes).**
    """
    found = {name: read_swagger_ui_asset(name) for name in SWAGGER_UI_ASSET_NAMES}
    testbase.assert_equal(
        {name: (value[1], len(value[0]) > 500) for name, value in found.items()},
        {"swagger-ui-bundle.js": ("application/javascript", True), "swagger-ui.css": ("text/css", True), "favicon-32x32.png": ("image/png", True)},
    )
    return


def test_no_other_file_is_handed_out_whatever_it_is_called():
    """
        **Feature: Swagger UI page**
        **Property: any name outside the allowlist (ReDoc's script, the manifest, names that climb out of the directory, an empty name) gets ``None`` and no file content.**
    """
    names = ("redoc.standalone.js", "manifest.json", "../manifest.json", "..%2fmanifest.json", "../../static/manifest.json", "swagger-ui.css.map", "")
    testbase.assert_equal([read_swagger_ui_asset(name) for name in names], [None] * len(names))
    return
