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

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint, Router
from ccai.webworks.openapi.assets import AssetResolver

if TYPE_CHECKING:
    from ccai.webworks.openapi.generator import OpenAPIGenerator


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
