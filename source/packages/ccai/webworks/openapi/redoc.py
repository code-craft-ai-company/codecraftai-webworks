"""
.. module:: redoc
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: ReDoc blueprint for serving alternative API documentation
        using the ReDoc rendering engine.

.. moduleauthor:: Code Craft AI LLC

This module provides the ReDoc_Blueprint class that extends RestBlueprint
to serve the ReDoc documentation interface. ReDoc provides a clean,
responsive, three-panel documentation layout. Unlike the Swagger UI
blueprint, ReDoc only serves the UI page and points to an existing
OpenAPI specification URL (typically served by the Swagger UI blueprint).
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restblueprint import RestBlueprint, Router
from ccai.webworks.openapi.assets import AssetResolver


REDOC_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - API Documentation</title>
    <style>
        body {{ margin: 0; padding: 0; }}
    </style>
</head>
<body>
    <redoc spec-url="{spec_url}" {extra_config}></redoc>
    <script src="{static_path}/redoc.standalone.js"></script>
</body>
</html>
"""


class ReDocBlueprint(RestBlueprint):
    """
        Blueprint that serves ReDoc API documentation.

        This blueprint extends RestBlueprint to provide a single endpoint
        serving the ReDoc documentation interface. ReDoc renders a clean,
        responsive, three-panel documentation layout from an OpenAPI
        specification.

        Unlike the Swagger_UI_Blueprint, ReDoc does not serve the OpenAPI
        specification itself. Instead, it points to an existing specification
        URL via the spec_url parameter. This allows both Swagger UI and
        ReDoc to share the same specification endpoint.

        :param generator: The OpenAPI_Generator instance used to retrieve
            the API title for the page heading.
        :param ui_path: URL path for the ReDoc page. Defaults to "/redoc".
        :param spec_url: URL of the OpenAPI specification JSON endpoint.
            Defaults to "/openapi.json".
        :param static_path: URL base path for serving bundled static assets.
            Defaults to "/_redoc".
        :param redoc_config: Additional ReDoc configuration options passed
            as keyword arguments. These are rendered as attributes on the
            redoc HTML element (e.g., hideDownloadButton, expandResponses).
    """

    base_path = "/redoc"

    def __init__(
        self,
        generator: "OpenAPI_Generator",
        ui_path: str = "/redoc",
        spec_url: str = "/openapi.json",
        static_path: str = "/_redoc",
        **redoc_config
    ):
        self.generator = generator
        self.ui_path = ui_path
        self.spec_url = spec_url
        self.static_path = static_path
        self.redoc_config = redoc_config
        self._asset_resolver = AssetResolver()

        return

    def serve_ui(self) -> Tuple[str, int, Dict[str, str]]:
        """
            Serve the ReDoc HTML page.

            Generates an HTML page containing the ReDoc documentation
            interface configured to load the OpenAPI specification from
            the configured spec_url.  All asset references point to the
            local static_path rather than external CDNs.

            :returns: A tuple of (html_content, status_code, headers) where
                headers include Content-Type set to text/html.
        """
        html_content = self._build_redoc_html()
        headers = {"Content-Type": "text/html"}

        return (html_content, 200, headers)

    def serve_static(self, filename: str) -> Tuple[bytes, int, Dict[str, str]]:
        """
            Serve a bundled ReDoc static asset.

            Reads the requested file from the vendored redoc asset group
            using the AssetResolver.  Sets Content-Type based on the file
            extension and Cache-Control for long-lived immutable caching.

            :param filename: The asset filename (e.g. 'redoc.standalone.js').

            :returns: A tuple of (content_bytes, status_code, headers).
                Returns a 404 response with an empty body when the
                requested file is not found.
        """
        content = self._asset_resolver.resolve("redoc", filename)

        if content is None:
            headers = {"Content-Type": "text/plain"}
            return (b"Not Found", 404, headers)

        content_type = self._asset_resolver.content_type(filename)
        headers = {
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000, immutable",
        }

        return (content, 200, headers)

    def _build_redoc_html(self) -> str:
        """
            Build the ReDoc HTML page with the current configuration.

            Formats the REDOC_HTML_TEMPLATE with the configured specification
            URL, title from the generator info, and all ReDoc configuration
            options rendered as HTML attributes on the redoc element.

            :returns: A string containing the complete HTML page.
        """
        title = self.generator.info.title

        extra_config_parts = []
        for key, value in self.redoc_config.items():
            if isinstance(value, bool):
                attr_value = "true" if value else "false"
            elif isinstance(value, str):
                attr_value = value
            else:
                attr_value = str(value)
            extra_config_parts.append(f'{key}="{attr_value}"')

        extra_config = " ".join(extra_config_parts)

        html = REDOC_HTML_TEMPLATE.format(
            title=title,
            spec_url=self.spec_url,
            static_path=self.static_path,
            extra_config=extra_config,
        )

        return html

    def get_descriptors(self) -> List[EndpointDescriptor]:
        """
            Create endpoint descriptors for the ReDoc UI and static routes.

            Builds EndpointDescriptor objects for the ReDoc documentation
            page and the static asset serving endpoint.  Unlike Swagger UI,
            ReDoc does not need a separate spec endpoint since it references
            an existing specification URL.

            :returns: A list of EndpointDescriptor objects for the ReDoc
                UI and static asset routes.
        """
        ui_descriptor = EndpointDescriptor(
            handler=self.serve_ui,
            module=self.__class__.__module__,
            path=self.ui_path,
            methods=["GET"],
            tags=["documentation"],
            doc=Doc(
                summary="ReDoc API Documentation",
                description="API documentation powered by ReDoc.",
            ),
        )

        static_descriptor = EndpointDescriptor(
            handler=self.serve_static,
            module=self.__class__.__module__,
            path=self.static_path + "/<filename>",
            methods=["GET"],
            tags=["documentation"],
            doc=Doc(
                summary="ReDoc Static Assets",
                description="Bundled static assets for the ReDoc interface.",
            ),
        )

        return [ui_descriptor, static_descriptor]

    @classmethod
    def register(
        cls,
        router: Optional[Router] = None,
        instance: Optional["ReDoc_Blueprint"] = None,
    ) -> List[EndpointDescriptor]:
        """
            Register ReDoc routes and return their descriptors.

            This method overrides the base RestBlueprint register to create
            EndpointDescriptors programmatically for the ReDoc UI route
            rather than relying on attach_at decorators. An instance must
            be provided since the blueprint is configured at runtime.

            :param router: Optional router to add endpoints to.
            :param instance: The ReDoc_Blueprint instance containing
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
