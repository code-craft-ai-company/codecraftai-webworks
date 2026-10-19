"""
.. module:: swaggerui
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Swagger UI blueprint for serving interactive API documentation
        and the OpenAPI specification from bundled static assets.

.. moduleauthor:: Code Craft AI LLC

This module provides the SwaggerUIBlueprint class that extends RestBlueprint
to serve the Swagger UI interactive documentation interface and the generated
OpenAPI specification as JSON. All static assets (JavaScript, CSS, favicon) are
served from vendored files bundled within the package so that no external CDN
requests are made at runtime.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import html
import json

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint, Router
from ccai.webworks.openapi.assets import AssetResolver

if TYPE_CHECKING:
    from ccai.webworks.openapi.generator import OpenAPIGenerator

#: The files of the vendored Swagger UI that a page needs, and the only ones :func:`read_swagger_ui_asset` will hand out.
SWAGGER_UI_ASSET_NAMES: Tuple[str, ...] = ("swagger-ui-bundle.js", "swagger-ui.css", "favicon-32x32.png")

#: The name the starter script is served under next to the assets (see :func:`render_swagger_ui_initializer`).
SWAGGER_UI_INITIALIZER_NAME: str = "swagger-initializer.js"

#: The values Swagger UI accepts for ``docExpansion``.
SWAGGER_UI_DOC_EXPANSIONS: Tuple[str, ...] = ("none", "list", "full")


SWAGGER_UI_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Swagger UI</title>
    <link rel="stylesheet" href="{static_path}/swagger-ui.css">
    <link rel="icon" type="image/png" href="{static_path}/favicon-32x32.png" sizes="32x32">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="{static_path}/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: "{spec_url}",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis
                ],
                tryItOutEnabled: {try_it_out},
                docExpansion: "{doc_expansion}",
                filter: {filter},
                {extra_config}
            }});
        }};
    </script>
</body>
</html>
"""


class SwaggerUIBlueprint(RestBlueprint):
    """
        Blueprint that serves Swagger UI from bundled assets and the
        OpenAPI specification.  No external CDN requests are made.

        This blueprint extends RestBlueprint to provide three endpoint
        groups: the interactive Swagger UI HTML page, the generated
        OpenAPI specification as JSON, and a static asset route that
        serves the vendored JavaScript, CSS, and image files.

        :param generator: The OpenAPIGenerator instance used to produce
            the specification JSON.
        :param ui_path: URL path for the Swagger UI page. Defaults to "/docs".
        :param spec_path: URL path for the OpenAPI JSON specification.
            Defaults to "/openapi.json".
        :param static_path: URL base path for serving bundled static assets.
            Defaults to "/_swagger".
        :param try_it_out: Whether the "Try it out" feature is enabled
            in Swagger UI. Defaults to True.
        :param doc_expansion: The default expansion setting for operations
            in Swagger UI. Defaults to "list".
        :param filter: Whether the filter bar is enabled in Swagger UI.
            Defaults to True.
        :param swagger_config: Additional Swagger UI configuration options
            passed as keyword arguments.
    """

    base_path = "/docs"

    def __init__(
        self,
        generator: "OpenAPIGenerator",
        ui_path: str = "/docs",
        spec_path: str = "/openapi.json",
        static_path: str = "/_swagger",
        try_it_out: bool = True,
        doc_expansion: str = "list",
        filter: bool = True,
        **swagger_config
    ):
        self.generator = generator
        self.ui_path = ui_path
        self.spec_path = spec_path
        self.static_path = static_path
        self.try_it_out = try_it_out
        self.doc_expansion = doc_expansion
        self.filter = filter
        self.swagger_config = swagger_config
        self._asset_resolver = AssetResolver()

        return

    def serve_ui(self) -> Tuple[str, int, Dict[str, str]]:
        """
            Serve the Swagger UI HTML page.

            Generates an HTML page containing the Swagger UI interface
            configured to load the OpenAPI specification from the
            configured spec_path.  All asset references point to the
            local static_path rather than external CDNs.

            :returns: A tuple of (html_content, status_code, headers) where
                headers include Content-Type set to text/html.
        """
        html_content = self._build_swagger_html()
        headers = {"Content-Type": "text/html"}

        return (html_content, 200, headers)

    def serve_spec(self) -> Tuple[str, int, Dict[str, str]]:
        """
            Serve the OpenAPI specification as JSON.

            Uses the generator to produce the OpenAPI specification
            and returns it as a JSON string with appropriate headers.

            :returns: A tuple of (json_content, status_code, headers) where
                headers include Content-Type set to application/json.
        """
        json_content = self.generator.generate_json()
        headers = {"Content-Type": "application/json"}

        return (json_content, 200, headers)

    def serve_static(self, filename: str) -> Tuple[bytes, int, Dict[str, str]]:
        """
            Serve a bundled Swagger UI static asset.

            Reads the requested file from the vendored swagger-ui asset
            group using the AssetResolver.  Sets Content-Type based on
            the file extension and Cache-Control for long-lived immutable
            caching.

            :param filename: The asset filename (e.g. 'swagger-ui-bundle.js').

            :returns: A tuple of (content_bytes, status_code, headers).
                Returns a 404 response with an empty body when the
                requested file is not found.
        """
        content = self._asset_resolver.resolve("swagger-ui", filename)

        if content is None:
            headers = {"Content-Type": "text/plain"}
            return (b"Not Found", 404, headers)

        content_type = self._asset_resolver.content_type(filename)
        headers = {
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000, immutable",
        }

        return (content, 200, headers)

    def _build_swagger_html(self) -> str:
        """
            Build the Swagger UI HTML page with the current configuration.

            Formats the SWAGGER_UI_HTML_TEMPLATE with the configured
            specification URL, title from the generator info, static asset
            path, and all Swagger UI options.  The generated HTML references
            only local asset paths and contains no external CDN URLs.

            :returns: A string containing the complete HTML page.
        """
        title = self.generator.info.title

        try_it_out_js = "true" if self.try_it_out else "false"
        filter_js = "true" if self.filter else "false"

        extra_config_parts = []
        for key, value in self.swagger_config.items():
            if isinstance(value, bool):
                js_value = "true" if value else "false"
            elif isinstance(value, str):
                js_value = f'"{value}"'
            else:
                js_value = str(value)
            extra_config_parts.append(f"{key}: {js_value}")

        extra_config = ",\n                ".join(extra_config_parts)

        html = SWAGGER_UI_HTML_TEMPLATE.format(
            title=title,
            spec_url=self.spec_path,
            static_path=self.static_path,
            try_it_out=try_it_out_js,
            doc_expansion=self.doc_expansion,
            filter=filter_js,
            extra_config=extra_config,
        )

        return html

    def get_descriptors(self) -> List[EndpointDescriptor]:
        """
            Create endpoint descriptors for the UI, spec, and static routes.

            Builds EndpointDescriptor objects for the Swagger UI page,
            the OpenAPI specification JSON endpoint, and the static asset
            serving endpoint.  These descriptors can be used for router
            registration.

            :returns: A list of EndpointDescriptor objects for the UI,
                spec, and static asset routes.
        """
        ui_descriptor = EndpointDescriptor(
            handler=self.serve_ui,
            module=self.__class__.__module__,
            path=self.ui_path,
            methods=["GET"],
            tags=["documentation"],
            doc=Doc(
                summary="Swagger UI",
                description="Interactive API documentation powered by Swagger UI.",
            ),
        )

        spec_descriptor = EndpointDescriptor(
            handler=self.serve_spec,
            module=self.__class__.__module__,
            path=self.spec_path,
            methods=["GET"],
            tags=["documentation"],
            doc=Doc(
                summary="OpenAPI Specification",
                description="OpenAPI 3.0 specification in JSON format.",
            ),
        )

        static_descriptor = EndpointDescriptor(
            handler=self.serve_static,
            module=self.__class__.__module__,
            path=self.static_path + "/<filename>",
            methods=["GET"],
            tags=["documentation"],
            doc=Doc(
                summary="Swagger UI Static Assets",
                description="Bundled static assets for the Swagger UI interface.",
            ),
        )

        return [ui_descriptor, spec_descriptor, static_descriptor]

    @classmethod
    def register(
        cls,
        router: Optional[Router] = None,
        instance: Optional["SwaggerUIBlueprint"] = None,
    ) -> List[EndpointDescriptor]:
        """
            Register Swagger UI routes and return their descriptors.

            This method overrides the base RestBlueprint register to create
            EndpointDescriptors programmatically for the UI, spec, and
            static asset routes rather than relying on attach_at decorators.
            An instance must be provided since the blueprint is configured
            at runtime.

            :param router: Optional router to add endpoints to.
            :param instance: The SwaggerUIBlueprint instance containing
                the runtime configuration. If None, falls back to the
                parent class register behavior.

            :returns: A list of EndpointDescriptor objects for the registered routes.
        """
        if instance is None:
            return super().register(router=router)

        descriptors = instance.get_descriptors()

        if router is not None:
            for descriptor in descriptors:
                router.add_endpoint(descriptor)

        return descriptors


@dataclass(frozen=True)
class SwaggerUIOptions:
    """
        How a Swagger UI page behaves.

        :param try_it_out_enabled: Open every operation already in "Try it out" mode. Off, a person clicks **Try it out** and then
                                   **Execute**: two deliberate steps before a request is sent.
        :param doc_expansion: ``none`` (everything folded; the person opens what they want), ``list`` (groups open, operations folded)
                              or ``full`` (everything open).
        :param filter: Show the filter box (it matches group names).
        :param deep_linking: Keep the open group or operation in the page address, so a link opens it.
        :param default_models_expand_depth: How far the Schemas block at the bottom is opened; ``-1`` hides it.
        :param operations_sorter: ``alpha`` (by path), ``method`` or ``""`` for the document's own order.
        :param tags_sorter: ``alpha`` or ``""`` for the document's own order.
        :param supported_submit_methods: The HTTP methods Try it out may send (lower case). ``None`` allows every method; an empty
                                         tuple removes Try it out altogether; ``("get",)`` makes the page safe to leave open on a
                                         production system.
    """
    try_it_out_enabled: bool = False
    doc_expansion: str = "none"
    filter: bool = True
    deep_linking: bool = True
    default_models_expand_depth: int = -1
    operations_sorter: str = "alpha"
    tags_sorter: str = "alpha"
    supported_submit_methods: Optional[Tuple[str, ...]] = None


def build_swagger_ui_config(
        *,
        spec_url: str,
        options: Optional[SwaggerUIOptions] = None,
        extra: Optional[Mapping[str, Any]] = None
    ) -> Dict[str, Any]:
    """
        The configuration object a page passes to ``SwaggerUIBundle``.

        :param spec_url: Where the page loads the OpenAPI document from.
        :param options: The page's behaviour; the defaults of :class:`SwaggerUIOptions` when ``None``.
        :param extra: More Swagger UI settings, which win over the ones above.

        :returns: The configuration as a JSON-serialisable dict (the ``presets`` are added by the starter script, since they are code).

        :raises: ValueError when ``doc_expansion`` is not one of :data:`SWAGGER_UI_DOC_EXPANSIONS`.
    """
    chosen = options if options is not None else SwaggerUIOptions()

    if chosen.doc_expansion not in SWAGGER_UI_DOC_EXPANSIONS:
        raise ValueError(
            "doc_expansion must be one of {}, not '{}'".format(", ".join(SWAGGER_UI_DOC_EXPANSIONS), chosen.doc_expansion)
        )

    rtnval: Dict[str, Any] = {
        "url": spec_url,
        "dom_id": "#swagger-ui",
        "tryItOutEnabled": chosen.try_it_out_enabled,
        "docExpansion": chosen.doc_expansion,
        "filter": chosen.filter,
        "deepLinking": chosen.deep_linking,
        "defaultModelsExpandDepth": chosen.default_models_expand_depth,
    }
    if len(chosen.operations_sorter) > 0:
        rtnval["operationsSorter"] = chosen.operations_sorter
    if len(chosen.tags_sorter) > 0:
        rtnval["tagsSorter"] = chosen.tags_sorter
    if chosen.supported_submit_methods is not None:
        rtnval["supportedSubmitMethods"] = [method.lower() for method in chosen.supported_submit_methods]
    if extra is not None:
        rtnval.update(dict(extra))

    return rtnval


def render_swagger_ui_initializer(
        *,
        spec_url: str,
        options: Optional[SwaggerUIOptions] = None,
        extra: Optional[Mapping[str, Any]] = None
    ) -> str:
    """
        The script that starts Swagger UI on a page made by :func:`render_swagger_ui_page`. It is a file of its own, served beside the
        library, because a page whose Content-Security-Policy allows scripts from its own origin only cannot hold an inline starter.

        :param spec_url: Where the page loads the OpenAPI document from.
        :param options: The page's behaviour.
        :param extra: More Swagger UI settings.

        :returns: JavaScript text.
    """
    config = build_swagger_ui_config(spec_url=spec_url, options=options, extra=extra)
    config_text = json.dumps(config, indent=4, sort_keys=True).replace("\n", "\n    ")

    lines = [
        "window.onload = function () {",
        "    var config = {};".format(config_text),
        "    config.presets = [SwaggerUIBundle.presets.apis];",
        "    window.ui = SwaggerUIBundle(config);",
        "};",
        "",
    ]
    rtnval = "\n".join(lines)
    return rtnval


def render_swagger_ui_page(
        *,
        title: str,
        static_path: str,
        initializer_name: str = SWAGGER_UI_INITIALIZER_NAME
    ) -> str:
    """
        The Swagger UI page: a container, the library's style and script, and the starter script, all loaded from ``static_path``. The
        page holds no script of its own and names no other host.

        :param title: The page title (the API's name).
        :param static_path: The URL path the assets and the starter are served under (no trailing slash).
        :param initializer_name: The starter script's file name under ``static_path``.

        :returns: HTML text.
    """
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "    <title>{} - Swagger UI</title>".format(html.escape(title)),
        '    <link rel="stylesheet" href="{}/swagger-ui.css">'.format(html.escape(static_path)),
        '    <link rel="icon" type="image/png" href="{}/favicon-32x32.png" sizes="32x32">'.format(html.escape(static_path)),
        "</head>",
        "<body>",
        '    <div id="swagger-ui"></div>',
        '    <script src="{}/swagger-ui-bundle.js"></script>'.format(html.escape(static_path)),
        '    <script src="{}/{}"></script>'.format(html.escape(static_path), html.escape(initializer_name)),
        "</body>",
        "</html>",
        "",
    ]
    rtnval = "\n".join(lines)
    return rtnval


def read_swagger_ui_asset(filename: str) -> Optional[Tuple[bytes, str]]:
    """
        One of the vendored Swagger UI files, by name. Only the names in :data:`SWAGGER_UI_ASSET_NAMES` are served: any other name,
        including one that climbs out of the asset directory, is refused, so a route that serves these files never serves anything else.

        :param filename: The requested file name.

        :returns: ``(content, content type)``, or ``None`` when the name is not one of the Swagger UI files or the file is missing.
    """
    if filename not in SWAGGER_UI_ASSET_NAMES:
        return None

    resolver = AssetResolver()
    content = resolver.resolve("swagger-ui", filename)
    if content is None:
        return None

    rtnval = (content, resolver.content_type(filename))
    return rtnval
