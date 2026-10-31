"""
    Tests for the API explorer page, starter script and asset helpers.

    A page whose Content-Security-Policy allows scripts from its own origin only cannot hold an inline starter, so the page and the starter script are
    separate files, the options are explicit, and only the explorer's own files and the vendored Swagger UI files are ever handed out.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []

import json
import re

from ccai import testbase

from ccai.webworks.openapi.explorer import (
    EXPLORER_ASSET_NAMES,
    EXPLORER_INITIALIZER_NAME,
    EXPLORER_OWN_ASSET_NAMES,
    ExplorerOptions,
    build_explorer_config,
    read_explorer_asset,
    render_explorer_initializer,
    render_explorer_page,
)
from ccai.webworks.openapi.swaggerui import SWAGGER_UI_ASSET_NAMES


def test_the_page_loads_the_library_the_model_the_page_script_and_the_starter_in_that_order_and_holds_no_script_of_its_own():
    """
        **Feature: API explorer page**
        **Property: the page has the explorer container, two style sheets and four ``<script src>`` elements under the asset path (Swagger UI, the model, the
        page script, the starter, in that order), no script body, and no address on another host.**
    """
    page = render_explorer_page(title="Demo API", static_path="/docs/assets")
    scripts = re.findall(r"<script\b([^>]*)>(.*?)</script>", page, re.S)
    sources = [re.search(r'src="([^"]+)"', attributes).group(1) for attributes, _body in scripts]
    testbase.assert_equal(
        (
            'id="explorer"' in page,
            sources,
            [body.strip() for _attributes, body in scripts],
            "http://" in page or "https://" in page,
            "<title>Demo API - API explorer</title>" in page,
            re.findall(r'<link rel="stylesheet" href="([^"]+)"', page),
        ),
        (
            True,
            [
                "/docs/assets/swagger-ui-bundle.js", "/docs/assets/explorer-model.js", "/docs/assets/explorer.js",
                "/docs/assets/{}".format(EXPLORER_INITIALIZER_NAME),
            ],
            ["", "", "", ""],
            False,
            True,
            ["/docs/assets/swagger-ui.css", "/docs/assets/explorer.css"],
        ),
    )
    return


def test_the_page_escapes_the_title_and_paths_it_is_given():
    """
        **Feature: API explorer page**
        **Property: markup in the title or in the asset path is escaped, never written into the page as markup.**
    """
    page = render_explorer_page(title="<script>alert(1)</script>", static_path='/a"b')
    testbase.assert_equal(("<script>alert" in page, "&lt;script&gt;alert(1)&lt;/script&gt;" in page, '"/a"b/' in page), (False, True, False))
    return


def test_the_default_configuration_names_the_document_and_leaves_try_it_out_to_a_person():
    """
        **Feature: API explorer page**
        **Property: the default configuration holds the document address, the title and ``tryItOutEnabled: false`` (a person clicks Try it out, then Execute),
        and leaves ``supportedSubmitMethods`` out so every method is allowed.**
    """
    config = build_explorer_config(document_url="/api/v1/openapi.json", title="Demo API")
    testbase.assert_equal(config, {"documentUrl": "/api/v1/openapi.json", "title": "Demo API", "tryItOutEnabled": False})
    return


def test_try_it_out_can_be_limited_to_get_or_removed():
    """
        **Feature: API explorer page**
        **Property: ``supported_submit_methods`` of ``("GET",)`` becomes ``["get"]``, ``()`` becomes ``[]`` (no Try it out), and ``None`` leaves the setting
        out.**
    """
    get_only = build_explorer_config(document_url="/o.json", title="T", options=ExplorerOptions(supported_submit_methods=("GET",)))
    none = build_explorer_config(document_url="/o.json", title="T", options=ExplorerOptions(supported_submit_methods=()))
    everything = build_explorer_config(document_url="/o.json", title="T", options=ExplorerOptions(supported_submit_methods=None))
    testbase.assert_equal(
        (get_only["supportedSubmitMethods"], none["supportedSubmitMethods"], "supportedSubmitMethods" in everything),
        (["get"], [], False),
    )
    return


def test_the_starter_script_starts_the_explorer_with_the_configuration():
    """
        **Feature: API explorer page**
        **Property: the starter script calls ``CCAIApiExplorer.start`` with a configuration whose JSON is exactly the configuration built for the same
        arguments.**
    """
    options = ExplorerOptions(supported_submit_methods=("GET", "POST"), try_it_out_enabled=True)
    script = render_explorer_initializer(document_url="/api/v1/openapi.json", title="Demo API", options=options)
    match = re.search(r"var config = (\{.*?\n    \});", script, re.S)
    parsed = json.loads(match.group(1).replace("\n    ", "\n"))
    testbase.assert_equal(parsed, build_explorer_config(document_url="/api/v1/openapi.json", title="Demo API", options=options))
    testbase.assert_equal(("window.CCAIApiExplorer.start(config);" in script, "http://" in script or "https://" in script), (True, False))
    return


def test_only_the_explorer_files_and_the_swagger_ui_files_are_handed_out():
    """
        **Feature: API explorer page**
        **Property: every name in the allowlist reads back with a content type; a name that is not on it (another file in the directory, a path that climbs
        out of it, an empty name) is refused.**
    """
    served = {name: read_explorer_asset(name) for name in EXPLORER_ASSET_NAMES}
    testbase.assert_equal([name for name, found in served.items() if found is None], [])
    testbase.assert_equal(
        {name: served[name][1] for name in EXPLORER_OWN_ASSET_NAMES},
        {"explorer-model.js": "application/javascript", "explorer.js": "application/javascript", "explorer.css": "text/css"},
    )
    testbase.assert_equal(set(EXPLORER_ASSET_NAMES), set(SWAGGER_UI_ASSET_NAMES) | set(EXPLORER_OWN_ASSET_NAMES))
    refused = [read_explorer_asset(name) for name in ("manifest.json", "../manifest.json", "../../assets.py", "explorer/explorer.js", "")]
    testbase.assert_equal(refused, [None, None, None, None, None])
    return


def test_the_explorer_files_use_nothing_a_strict_content_security_policy_forbids():
    """
        **Feature: API explorer page**
        **Property: the explorer's scripts hold no ``eval``, no ``new Function``, no string timers and no address on another host, and its style sheet loads
        nothing from another host, so the page works under a policy that allows scripts and requests from its own origin only.**
    """
    problems = []
    for name in EXPLORER_OWN_ASSET_NAMES:
        text = read_explorer_asset(name)[0].decode("utf-8")
        for pattern in (r"\beval\s*\(", r"new\s+Function\s*\(", r"setTimeout\s*\(\s*[\"']", r"setInterval\s*\(\s*[\"']", r"https?://", r"@import"):
            if re.search(pattern, text):
                problems.append((name, pattern))
    testbase.assert_equal(problems, [])
    return
